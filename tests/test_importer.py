import os
import sys

from unittest2 import TestCase

from elcap import importer
from elcap.importer import get_package
from elcap.plugins import unload_modules

class TestImporter(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_modules = sys.modules.keys()

    def setUp(self):
        self.importer = importer.ModuleImporter()

    def tearDown(self):
        unload_modules(exclude=self.base_modules)
        self.importer.uninstall()

    def test_register_one_module(self):
        self.importer.register('testmodule', compile('pi = "3.141592..."', os.path.join(os.path.dirname(__file__), 'testmodule.py'), 'exec'))
        import testmodule
        self.assertEquals(testmodule.pi, "3.141592...")

    def test_uninstall(self):
        self.importer.register('testmodule', compile('pi = "3.141592..."', os.path.join(os.path.dirname(__file__), 'testmodule.py'), 'exec'))
        self.importer.uninstall()
        import testmodule
        self.assertEquals(testmodule.pi, 3.1415926535)

    def test_importer_is_in_first_position(self):
        new_importer = importer.ModuleImporter()
        self.assertEquals(sys.meta_path[0], new_importer)

    def test_looking_for_unregistered_module(self):
        import testmodule
        self.assertEquals(testmodule.pi, 3.1415926535)

    def test_check_required_attributes_are_present(self):
        self.importer.register('testmodule', compile('pi = "3.141592..."', os.path.join(os.path.dirname(__file__), 'testmodule.py'), 'exec'))
        import testmodule
        self.assertEquals(self.importer, testmodule.__loader__)
        self.assertEquals('testmodule.py', os.path.basename(testmodule.__file__))

    def test_import_error_raised_when_loading_non_registered_module(self):
        with self.assertRaises(ImportError):
            self.importer.load_module('unknown_module')

    def test_import_submodule(self):
        self.importer.register('testpackage.testmodule', compile('pi = "3.141592..."', os.path.join(os.path.dirname(__file__), 'testpackage/testmodule.py'), 'exec'))
        import testpackage.testmodule
        self.assertEquals('testpackage', testpackage.testmodule.__package__)

    def test_import_submodule_importing_from_module(self):
        self.importer.register('testpackage.testmodule2', compile('from testmodule import foo', os.path.join(os.path.dirname(__file__), 'testpackage/testmodule.py'), 'exec'))
        import testpackage.testmodule2
        self.assertEquals('foo', testpackage.testmodule2.foo)

    def test_import_package(self):
        self.importer.register('testpackage', compile('bar = "bar"', os.path.join(os.path.dirname(__file__), 'testpackage/__init__.py'), 'exec'))
        import testpackage
        self.assertEquals('bar', testpackage.bar)
        self.assertEquals('testpackage', testpackage.__package__)
        self.assertEquals([os.path.join(os.path.dirname(__file__), 'testpackage')], testpackage.__path__)

    def test_import_package_importing_submodule(self):
        self.importer.register('testpackage', compile('from testmodule import foo', os.path.join(os.path.dirname(__file__), 'testpackage/__init__.py'), 'exec'))
        import testpackage
        self.assertEquals('foo', testpackage.foo)

    def test_get_package(self):
        self.assertEquals('a.b', get_package('a.b.c', False))
        self.assertEquals('a.b.c', get_package('a.b.c', True))
        self.assertEquals('', get_package('a', False))
