import time

from nose.plugins import Plugin
from nose.core import TextTestRunner
from nose.selector import Selector
import nose.core

from mutator import StringMutator, NumberMutator, ArithmeticMutator
from mutator import LogicalMutator, ComparisonMutator, FlowMutator, LineMutator
import importer
import sys
import os
import coverage_plugin


class Quiet(Plugin):
    """Allows to run the tests and discard all the ouput."""

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self.enabled = True

    def setOutputStream(self, stream):
        return NullStream()


class NullStream(object):
    """File-like object that acts as /dev/null."""

    def write(self, *args):
        pass

    def flush(self):
        pass

    def writeln(self, *args):
        pass


class Mutations(Plugin):
    """Plugin that modifies the source code to check if the tests are really testing the code."""

    def options(self, parser, env):
        Plugin.options(self, parser, env)
        parser.add_option("--mutations-path", action="store",
                          default='.',
                          dest="mutations_path",
                          help="Restrict mutations to source files in this path (default: current working directory)")
        #parser.add_option("--mutations-exclude", action="append",
        #                  default=env.get('NOSE_MUTATIONS_EXCLUDE'),
        #                  dest="mutations_exclude",
        #                  help="Exclude mutations for source files found in this path"
        #                  "[NOSE_MUTATIONS_EXCLUDE]")

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.mutations_path = os.path.abspath(options.mutations_path or '.')
        #self.mutations_exclude = options.mutations_exclude or []
        self.failfast = config.stopOnError
        self.base_modules = sys.modules.keys()
        self.test_selector = Selector(config)

    def prepareTestRunner(self, runner):
        return MutationRunner(stream=runner.stream, failfast=self.failfast, base_modules=self.base_modules, mutations_path=self.mutations_path, test_selector=self.test_selector)


class MutationRunner(TextTestRunner):
    def __init__(self, **kw):
        failfast = kw.pop('failfast', False)
        self.mutations_path = kw.pop('mutations_path')
        self.test_selector = kw.pop('test_selector')
        self.base_modules = kw.pop('base_modules', [])
        super(MutationRunner, self).__init__(**kw)
        #We need to set the failfast option in this way because
        #nose.core.TextTestRunner hides some fields of unittest.TextTestRunner
        self.failfast = failfast

    def wantMutation(self, filename):
        return (filename.endswith('.py') and
               filename.startswith(self.mutations_path) and
               not self.test_selector.wantFile(filename) and
               os.path.exists(filename) and  # FIXME?: not that pythonic and get_source_mapping is alredy checking this
               os.path.getsize(filename) > 0)

    def run(self, test):
        quiet = Quiet()
        tcoverage = coverage_plugin.TestCoverage()

        #TODO: add data to result
        result = self._makeResult()

        self.stream.writeln('Running original tests')
        self.stream.writeln('-' * 70)

        #TODO: move this to init for testing
        #remove mutations plugin from argv to avoid infinite recursion
        args = list(sys.argv)
        if '--with-mutations' in args:
            args.remove('--with-mutations')
        #run all specified tests using the by test coverage
        success = nose.core.run(argv=args, addplugins=[tcoverage])

        module_source_mapping = get_module_source_mapping()
        #if one or more tests failed and the fail fast option is True then abort
        if not success:
            if self.failfast:
                return result
            else:
                self.stream.writeln('\Warning: Better results will be obtained if all tests pass. It is suggested to run this plugin with the -x (failfast) option.')

        self.stream.writeln('\nTesting mutated files')
        self.stream.writeln('-' * 70)
        start_time = time.time()

        source_filenames = [f for f in tcoverage.coverage_info.iterkeys() if self.wantMutation(f)]
        print source_filenames
        print tcoverage.coverage_info.keys()

        module_importer = importer.ModuleImporter()
        total_mutations = 0
        total_mutations_alive = 0

        #collect the by test coverage and mutate the files
        for source_filename in source_filenames:
            self.stream.write('%s: ' % source_filename)
            code = open(source_filename).read()
            #move this logic to line mutator
            for mutator in [StringMutator(), NumberMutator(), ArithmeticMutator(), LogicalMutator(), ComparisonMutator(), FlowMutator()]:
                for line_no, pos, m_node in LineMutator(mutator, code):
                    #TODO?: move this to the line mutator class
                    #TODO: skip lines matching a given pattern, to avoid mutating prints, logs, __author__, __version__, etc
                    if len(tcoverage.coverage_info[source_filename][line_no]) == 0:
                        continue
                    total_mutations += 1
                    unload_modules(exclude=self.base_modules)

                    module_importer.register(module_source_mapping[source_filename], compile(m_node, source_filename, 'exec'))

                    tests_set = tcoverage.coverage_info[source_filename][line_no]
                    #TODO: add plugin that limits the time a test can run (based on original times??)
                    success = nose.core.run(defaultTest=','.join(tests_set), argv=args + ['-x'], addplugins=[quiet])

                    if success:
                        #if the tests still pass and the fail fast option is True then abort
                        total_mutations_alive += 1
                        code_lines = code.split('\n')
                        self.stream.writeln('\nMutation survived at line %d, %s: %s' % (line_no, pos, code_lines[line_no - 1]))

                        #TODO: decide how to display the mutation. Coegen has really many problems and is really hard to fix it
                        #modified_source = codegen.to_source(m_node)
                        #TODO: generate a more accurate new source code, to resemble the original source code and show a more compact diff
                        #for l in difflib.unified_diff(code_lines, modified_source.split('\n'), source_filename + ' (original)', source_filename + ' (mutation-%d)' % pos):
                        #    self.stream.write('%s\n' % l.rstrip())

                        if self.failfast:
                            return result
                    else:
                        self.stream.write('.')
            self.stream.writeln()
        stop_time = time.time()
        self.stream.writeln('-' * 70)
        self.stream.writeln('%d mutations performed (survived %d) on %d files in %.3fs' % (total_mutations, total_mutations_alive, len(source_filenames), stop_time - start_time))
        return result


def unload_modules(exclude=None):
    """Unload all modules in sys.modules that are not found in exclude_modules."""
    exclude = set(exclude or [])
    for k in set(sys.modules.keys()) - exclude:
        del sys.modules[k]


def get_module_source_mapping():
    mapping = {}
    #FIXME?: I wanted to use iteritems instead but in some systems the modules changed during the iteration
    for module_name, module in sys.modules.items():
        if hasattr(module, '__file__') and module.__file__:
            filename = module.__file__
            src_filename = nose.util.src(filename)
            if src_filename == filename or not os.path.exists(src_filename):
                continue
            mapping[src_filename] = module_name
    return mapping
