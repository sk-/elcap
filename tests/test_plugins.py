import os

from unittest2 import TestCase
from unittest2 import TestSuite
from nose.plugins import PluginTester
from ludibrio import Stub

from elcap.plugins import Quiet
from elcap.coverage_plugin import TestCoverage

class TestTestCoveragePlugin(TestCase):
    def test_coverage(self):
        with Stub() as TestA:
            ta = TestA()
            ta.address() >> (__file__, None, 'testa')
        with Stub() as TestB:
            tb = TestB()
            tb.address() >> (__file__, None, 'testb')

        plugin = TestCoverage()
        plugin.begin()

        testa = TestA()
        plugin.beforeTest(testa)
        import testmodule
        testmodule.f()
        testmodule.g()
        plugin.afterTest(testa)

        testb = TestB()
        plugin.beforeTest(testb)
        import testmodule
        testmodule.g()
        plugin.afterTest(testb)

        testmodule_coverage = plugin.coverage_info[os.path.join(os.path.dirname(__file__), 'testmodule.py')]
        filename = __file__
        if __file__.endswith('.pyc'):
            filename = filename[:-1]
        self.assertIn('%s:testa' % filename, testmodule_coverage[3])
        self.assertIn('%s:testa' % filename, testmodule_coverage[5])
        self.assertIn('%s:testb' % filename, testmodule_coverage[5])

class TestQuietPluginWithPassingTest(PluginTester, TestCase):
    activate = ''  # enables the plugin
    plugins = [Quiet()]

    def test_is_enabled(self):
        self.assertTrue(self.plugins[0].enabled)

    def test_quiet_output(self):
        self.assertEquals(str(self.output), '')
        self.assertTrue(self.nose.success)

    def makeSuite(self):
        class TC(TestCase):
            def runTest(self):
                pass
        return TestSuite([TC()])


class TestQuietPluginWithFailingTest(PluginTester, TestCase):
    activate = ''  # enables the plugin
    plugins = [Quiet()]

    def test_quiet_output(self):
        self.assertEquals(str(self.output), '')
        self.assertFalse(self.nose.success)

    def makeSuite(self):
        class TC(TestCase):
            def runTest(self):
                raise ValueError("Failing test")
        return TestSuite([TC()])
