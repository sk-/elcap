import os
import sys
import imp


class ModuleImporter:
    '''
    Class that allows to replace modules.
    It is both a finder (find_module) and a loader (load_module).

    See PEP 302 (http://www.python.org/dev/peps/pep-0302/) for further details.

    This is a modified version of the code of Pymutester.
    '''
    def __init__(self):
        self.module_name = None
        self.module_code = None
        self.install()

    def install(self):
        if self not in sys.meta_path:
            sys.meta_path.insert(0, self)

    def uninstall(self):
        if self in sys.meta_path:
            sys.meta_path.remove(self)

    def register(self, module_name, module_code):
        self.module_name = module_name
        self.module_code = module_code

    def find_module(self, module_name, path=None):
        '''Returns self when the module registered is requested.'''
        if module_name == self.module_name:
            return self
        return None

    def load_module(self, module_name):
        '''Loads the registered module.'''
        if module_name != self.module_name:
            raise ImportError
        mod = sys.modules.setdefault(module_name, imp.new_module(module_name))
        mod.__file__ = self.module_code.co_filename  # required by PEP 302, only builtin modules are free to not have this attribute
        mod.__loader__ = self  # required by PEP 302
        #TODO: use nose.util.ispackage
        is_package = os.path.basename(mod.__file__) == '__init__.py'
        if is_package:
            mod.__path__ = [os.path.dirname(mod.__file__)]
        #TODO: use nose.util.getpackage
        package = get_package(module_name, is_package)
        if package:
            mod.__package__ = package
        exec self.module_code in mod.__dict__
        return mod


def get_package(module_name, is_package):
    if is_package:
        return module_name
    else:
        return '.'.join(module_name.split('.')[:-1])
