import time
import re

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

    def setOutputStream(self, stream):  # pylint: disable=C0103,W0613,R0201
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
    exclude_lines_pattern = '(__version__|__author__|(\s|^)print\s)'

    def options(self, parser, env):
        Plugin.options(self, parser, env)
        parser.add_option('--mutations-path', action='store',
                          default='.',
                          dest='mutations_path',
                          help='Restrict mutations to source files in this path (default: current working directory)')
        parser.add_option('--mutations-exclude', action='store', metavar='REGEX',
                          default=None,
                          dest='mutations_exclude',
                          help='Exclude mutations for source files containing this pattern (default: None)')
        parser.add_option('--mutations-exclude-lines', action='store', metavar='REGEX',
                          default='(__version__|__author__|^\s*print\s|^\s*raise\s)',
                          dest='mutations_exclude_lines',
                          help='Exclude mutations for lines containing this pattern (default: \'%s\'' % self.exclude_lines_pattern)

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.mutations_path = os.path.abspath(options.mutations_path or '.')
        self.mutations_exclude = None
        if options.mutations_exclude:
            self.mutations_exclude = re.compile(options.mutations_exclude)
        self.mutations_exclude_lines = re.compile(options.mutations_exclude_lines)
        self.failfast = config.stopOnError
        self.base_modules = sys.modules.keys()
        self.test_selector = Selector(config)

    def prepareTestRunner(self, runner):  # pylint: disable=C0103
        return MutationRunner(stream=runner.stream, failfast=self.failfast,
                              base_modules=self.base_modules,
                              mutations_path=self.mutations_path,
                              mutations_exclude=self.mutations_exclude,
                              mutations_exclude_lines=self.mutations_exclude_lines,
                              test_selector=self.test_selector)


class MutationRunner(TextTestRunner):
    def __init__(self, **kwargs):
        failfast = kwargs.pop('failfast', False)
        self.mutations_path = kwargs.pop('mutations_path', None)
        self.mutations_exclude = kwargs.pop('mutations_exclude', None)
        self.mutations_exclude_lines = kwargs.pop('mutations_exclude_lines', None)
        self.test_selector = kwargs.pop('test_selector', None)
        self.base_modules = kwargs.pop('base_modules', [])
        super(MutationRunner, self).__init__(**kwargs)
        #We need to set the failfast option in this way because
        #nose.core.TextTestRunner hides some fields of unittest.TextTestRunner
        self.failfast = failfast

    def want_mutation(self, filename):
        return (filename.endswith('.py') and
               filename.startswith(self.mutations_path) and
               not self.test_selector.wantFile(filename) and
               os.path.exists(filename) and  # FIXME?: not that pythonic and get_source_mapping is alredy checking this
               os.path.getsize(filename) > 0 and
               not (self.mutations_exclude and self.mutations_exclude.search(filename)))

    def _run_mutated_tests(self, source_filename, test_coverage, args):
        self.stream.write('%s: ' % source_filename)
        with open(source_filename) as fd:
            code = fd.read()
        code_lines = code.split('\n')
        #code_lines = get_lines(source_filename)
        #code = '\n'.join(code_lines)
        quiet = Quiet()
        #move this logic to line mutator
        for mutator in [StringMutator(), NumberMutator(), ArithmeticMutator(), LogicalMutator(), ComparisonMutator(), FlowMutator()]:
            for line_no, pos, m_node in LineMutator(mutator, code):
                #TODO?: move this to the line mutator class
                if len(test_coverage.coverage_info[source_filename][line_no]) == 0 or self.mutations_exclude_lines.search(code_lines[line_no - 1]):
                    continue
                self.total_mutations += 1
                unload_modules(exclude=self.base_modules)

                self.module_importer.register(self.module_source_mapping[source_filename], compile(m_node, source_filename, 'exec'))

                tests_set = test_coverage.coverage_info[source_filename][line_no]
                #TODO: add plugin that limits the time a test can run (based on original times??)
                success = nose.core.run(defaultTest=','.join(tests_set), argv=args + ['-x'], addplugins=[quiet])

                if success:
                    #if the tests still pass and the fail fast option is True then abort
                    self.total_mutations_alive += 1
                    self.stream.writeln('\nMutation survived at line %d (%s) using mutator %s:\n\t%s' % (line_no, pos, mutator.__class__.__name__, code_lines[line_no - 1].strip()))

                    #TODO: decide how to display the mutation. Codegen has really many problems and is really hard to fix it
                    #modified_source = codegen.to_source(m_node)
                    #TODO: generate a more accurate new source code, to resemble the original source code and show a more compact diff
                    #for l in difflib.unified_diff(code_lines, modified_source.split('\n'), source_filename + ' (original)', source_filename + ' (mutation-%d)' % pos):
                    #    self.stream.write('%s\n' % l.rstrip())

                    if self.failfast:
                        return False
                else:
                    self.stream.write('.')
        self.stream.writeln()
        return True

    def run(self, test):
        test_coverage = coverage_plugin.TestCoverage()

        #TODO: add data to result
        self.result = self._makeResult()

        self.stream.writeln('Running original tests')
        self.stream.writeln('-' * 70)

        #TODO: move this to init for testing
        #remove mutations plugin from argv to avoid infinite recursion
        args = list(sys.argv)
        if '--with-mutations' in args:
            args.remove('--with-mutations')
        #run all specified tests using the by test coverage plugin
        success = nose.core.run(argv=args, addplugins=[test_coverage])

        #if one or more tests failed and the fail fast option is True then abort
        if not success:
            if self.failfast:
                return self.result
            else:
                self.stream.writeln('\Warning: Better results will be obtained if all tests pass. It is suggested to run this plugin with the -x (failfast) option.')

        self.module_source_mapping = get_module_source_mapping()

        self.stream.writeln('\nTesting mutated files')
        self.stream.writeln('-' * 70)
        start_time = time.time()

        source_filenames = [f for f in test_coverage.coverage_info.iterkeys() if self.want_mutation(f)]
        print source_filenames
        print test_coverage.coverage_info.keys()

        self.module_importer = importer.ModuleImporter()
        self.total_mutations = 0
        self.total_mutations_alive = 0

        #collect the by test coverage and mutate the files
        for source_filename in source_filenames:
            if not self._run_mutated_tests(source_filename, test_coverage, args):
                return self.result

        stop_time = time.time()
        self.stream.writeln('-' * 70)
        self.stream.writeln('%d mutations performed (survived %d) on %d files in %.3fs' % (self.total_mutations, self.total_mutations_alive, len(source_filenames), stop_time - start_time))
        return self.result


def get_lines(filename):
    with open(filename) as fd:
        return fd.readlines()

def unload_modules(exclude=None):
    """Unload all modules in sys.modules that are not found in exclude_modules.

    Args:
        exclude (list): list of modules not to be unloaded.
    """
    exclude = set(exclude or [])
    for k in set(sys.modules.keys()) - exclude:
        del sys.modules[k]


def get_src_filename(filename):
    """Returns the filename of the source of a python resource (.py, .pyc, etc).

    Args:
        filename (str): the filanme of the python resource.
    Returns:
        A string representing the filename of the source or None if the resource
        or the source is not found.
    """ 
    src_filename = nose.util.src(filename)
    if not src_filename.endswith('.py') or not os.path.exists(src_filename):
        return None
    return src_filename


def get_module_source_mapping():
    """Returns a mapping from a source filename to its corresponding module."""
    mapping = {}
    #FIXME?: I wanted to use iteritems instead but in some systems the modules changed during the iteration
    for module_name, module in sys.modules.items():
        if hasattr(module, '__file__') and module.__file__:
            src_filename = get_src_filename(module.__file__)
            if src_filename:
                mapping[src_filename] = module_name
    return mapping
