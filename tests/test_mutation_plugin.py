from unittest2 import TestCase
from ludibrio import Stub
from ludibrio import any

from elcap.plugins import MutationRunner

class TestMutationRunner(TestCase):
    def test_init(self):
        runner = MutationRunner(failfast=True, base_modules=[None], mutations_path=None, test_selector=None)
        self.assertTrue(runner.failfast)

    def test_want_mutation_python_file(self):
        runner = MutationRunner(mutations_path=None, test_selector=None)
        #self.assertTrue(runner.wantMutation('/mutations/path/submodule/module.py'))
        self.assertFalse(runner.want_mutation('/mutations/path/submodule/module.pyc'))

    def test_want_mutation_file_in_mutations_path(self):
        runner = MutationRunner(mutations_path='/mutations/path', test_selector=None)
        #self.assertTrue(runner.wantMutation('/mutations/path/submodule/module.py'))
        self.assertFalse(runner.want_mutation('/mutations/submodule/module.py'))

    def test_want_mutation_selector(self):
        with Stub() as selector:
            selector.wantFile(any()) >> True
            #selector.wantFile(any()) >> False
        runner = MutationRunner(mutations_path='/mutations/path', test_selector=selector)
        self.assertFalse(runner.want_mutation('/mutations/path/submodule/module.py'))
        #self.assertTrue(runner.wantMutation('/mutations/path/submodule/module.py'))

    def test_want_mutation_nonexistent_file(self):
        with Stub() as selector:
            selector.wantFile(any()) >> False
        runner = MutationRunner(mutations_path='/mutations/path', test_selector=selector)
        self.assertFalse(runner.want_mutation('/mutations/path/submodule/module.py'))
        #self.assertTrue(runner.wantMutation('/mutations/path/submodule/module.py'))

    def xtest_want_mutation_emptyfile(self):
        with Stub() as selector:
            selector.wantFile(any()) >> False
        with Stub() as exists:
            from os.path import exists
            exists(any()) >> True
        with Stub() as getsize:
            from os.path import getsize
            getsize(any()) >> 0
            getsize(any()) >> 1024
        runner = MutationRunner(mutations_path='/mutations/path', test_selector=selector)
        self.assertFalse(runner.wantMutation('/mutations/path/submodule/module.py'))
        self.assertTrue(runner.wantMutation('/mutations/path/submodule/module.py'))
        exists.restore_import()
        getsize.restore_import()

    def test_run(self):
        with Stub() as selector:
            selector.wantFile(any()) >> False
        with Stub() as run:
            from nose.core import run
            run(argv=any(), addplugins=any()) >> True
        runner = MutationRunner(mutations_path='/mutations/path', test_selector=selector)
        runner.run(None)
