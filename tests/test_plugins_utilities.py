import os
import sys

from unittest2 import TestCase

from elcap import plugins


class TestUtilities(TestCase):
    def test_unload_all_modules(self):
        old_modules = dict(sys.modules)
        plugins.unload_modules()
        self.assertEquals(sys.modules, {})
        sys.modules = old_modules

    def test_unload_only_one_module(self):
        old_modules = dict(sys.modules)
        import testmodule
        plugins.unload_modules(old_modules)
        self.assertEquals(sys.modules, old_modules)

    def test_get_module_source_mapping(self):
        mapping = plugins.get_module_source_mapping()
        filename = __file__
        if filename.endswith('.pyc'):
            filename = filename[:-1]
        self.assertEquals(mapping[filename], __name__)
        for filename, module  in mapping.iteritems():
            self.assertTrue(filename.endswith('.py'), filename)
            self.assertTrue(os.path.exists(filename))
