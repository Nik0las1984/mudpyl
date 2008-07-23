from mudpyl.matchers import ProtoMatcher, BaseMatchingRealm
from mudpyl.realms import RootRealm
from mock import Mock, patch, sentinel
import traceback

class Test__call__:

    def setUp(self):
        self.m = ProtoMatcher(func = self.func)
        self.realm = Mock(spec = BaseMatchingRealm)
        self.realm.root = Mock(spec = RootRealm)
        self.matches = []

    def func(self, match, realm):
        self.matches.append(match)
        assert realm is self.realm

    def test_passes_on_match(self):
        o = object()
        self.m(o, self.realm)
        assert len(self.matches) == 1
        assert self.matches[0] is o

    def test_traces_calls(self):
        self.m(None, self.realm)
        arg = '%s matched!' % self.m
        assert self.realm.trace.call_args_list == [((arg,), {})]

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

class TestBaseMatchingRealm:

    def setUp(self):
        self.realm = BaseMatchingRealm(Mock(), Mock())

    def test_forwards_traces_to_parent(self):
        self.realm.trace(sentinel.trace)
        assert self.realm.parent.trace.call_args_list == [((sentinel.trace,),
                                                           {})]
