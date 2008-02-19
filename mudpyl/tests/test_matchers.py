from mudpyl.matchers import ProtoMatcher, BaseMatchingRealm
from mudpyl.realms import RootRealm
from mock import Mock, patch
import traceback

class Test__call__:

    def setUp(self):
        self.m = ProtoMatcher(func = self.func)
        self.realm = Mock(spec = BaseMatchingRealm)
        self.realm.root = Mock(spec = RootRealm)
        self.realm.root.tracing = False
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
        assert not self.realm.write.called

    def test_traces_if_told_to(self):
        self.realm.root.tracing = True
        self.m(None, self.realm)
        arg = ('TRACE: %s matched!' % self.m)
        print self.realm.write.call_args_list
        assert self.realm.write.call_args_list == [((arg,), {})]

    def bad_func(self, match, info):
        raise Exception

    @patch('mudpyl.matchers', 'traceback')
    def test_uses_traceback_on_error(self, t):
        self.m.func = self.bad_func
        self.m(None, self.realm)
        assert t.print_exc.called
 
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
