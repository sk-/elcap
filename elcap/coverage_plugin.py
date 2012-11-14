from collections import defaultdict

from nose.plugins.base import Plugin
import nose.util


class TestCoverage(Plugin):
    """
    Activate a by test coverage report using Ned Batchelder's coverage module.
    """

    def __init__(self):
        super(TestCoverage, self).__init__()
        self.coverage_info = defaultdict(lambda: defaultdict(set))
        self._cover_instance = None

    @property
    def cover_instance(self):
        if not self._cover_instance:
            import coverage
            try:
                self._cover_instance = coverage.coverage()
            except coverage.CoverageException:
                self._cover_instance = coverage
        return self._cover_instance

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self.enabled = True

    def begin(self):
        self.cover_instance.erase()
        self.cover_instance.exclude('#pragma[: ]+[nN][oO] [cC][oO][vV][eE][rR]')

    def beforeTest(self, test):  # pylint: disable=C0103,W0613
        self.cover_instance.start()

    def afterTest(self, test):  # pylint: disable=C0103
        self.cover_instance.stop()
        self.cover_instance.save()
        for covered_filename in self.cover_instance.data.measured_files():
            for line in self.cover_instance.data.lines[covered_filename]:
                self.coverage_info[covered_filename][line].add(
                    make_name(test.address()))
        self.cover_instance.erase()


def make_name(test_addr):
    filename, module, call = test_addr
    if filename is not None:
        head = nose.util.src(filename)
    else:
        head = module
    if call is not None:
        return '%s:%s' % (head, call)
    return head
