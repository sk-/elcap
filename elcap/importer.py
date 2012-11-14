import os
import sys
import imp


class ModuleImporter(object):
    """
    Class that allows to replace modules.
    It is both a finder (find_module) and a loader (load_module).

    See PEP 302 (http://www.python.org/dev/peps/pep-0302/) for further details.

    This is a modified version of the code of Pymutester.
    """
    def __init__(self):
        self.module_name = None
        self.module_code = None
        self.install()

    def install(self):
        """Install this importer before all others."""
        if self not in sys.meta_path:
            sys.meta_path.insert(0, self)

    def uninstall(self):
        """Removes this importer from the global importers."""
        if self in sys.meta_path:
            sys.meta_path.remove(self)

    def register(self, module_name, module_code):
        """Register a module to be loaded with this importer."""
        self.module_name = module_name
        self.module_code = module_code

    def find_module(self, module_name, path=None):  # pylint: disable=W0613
        """Returns self when the module registered is requested."""
        if module_name == self.module_name:
            return self
        return None

    def load_module(self, module_name):
        """Loads the registered module."""
        if module_name != self.module_name:
            raise ImportError
        mod = sys.modules.setdefault(module_name, imp.new_module(module_name))

        # The following two fields are required by PEP 302
        mod.__file__ = self.module_code.co_filename
        mod.__loader__ = self

        #TODO: use nose.util.ispackage
        is_package = os.path.basename(mod.__file__) == '__init__.py'
        if is_package:
            mod.__path__ = [os.path.dirname(mod.__file__)]
        #TODO: use nose.util.getpackage
        package = get_package(module_name, is_package)
        if package:
            mod.__package__ = package
        exec self.module_code in mod.__dict__  # pylint: disable=W0122
        return mod


def get_package(module_name, is_package):
    """Returns a string representing the package to which the file belongs."""
    if is_package:
        return module_name
    else:
        return '.'.join(module_name.split('.')[:-1])
