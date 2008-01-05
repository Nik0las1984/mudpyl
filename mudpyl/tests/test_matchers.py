from mudpyl.matchers import ProtoMatcher
from mudpyl import matchers
import traceback

class FakeRealm:

    def __init__(self):
        self.noted = []
        self.tracing = False
        self.root = self

    def write(self, string):
        self.noted.append(string)

class FakeTracebackModule:

    def __init__(self):
        self.print_exc_called = False

    def print_exc(self):
        assert not self.print_exc_called
        self.print_exc_called = True

class Test__call__:

    def setUp(self):
        self.m = ProtoMatcher(func = self.func)
        self.realm = FakeRealm()
        self.matches = []

    def func(self, match, realm):
        self.matches.append(match)
        assert realm is self.realm

    def test_passes_on_match(self):
        o = object()
        self.m(o, self.realm)
        assert len(self.matches) == 1
        assert self.matches[0] is o

    def test_doesnt_trace_if_told_not_to(self):
        self.m(None, self.realm)
        assert not self.realm.noted

    def test_traces_if_told_to(self):
        self.realm.tracing = True
        self.m(None, self.realm)
        assert self.realm.noted == ['TRACE: %s matched!' % self.m]

    def bad_func(self, match, info):
        raise Exception

    def test_uses_traceback_on_error(self):
        self.m.func = self.bad_func
        matchers.traceback = t = FakeTracebackModule()
        self.m(None, self.realm)
        assert t.print_exc_called
        matchers.traceback = traceback
 
    def simulated_grumpy_user(self, match, info):
        raise KeyboardInterrupt

    def test_allows_KeyboardInterrupt_through(self):
        self.m.func = self.simulated_grumpy_user
        try:
            self.m(None, self.realm)
        except KeyboardInterrupt:
            pass
        else:
            assert False
