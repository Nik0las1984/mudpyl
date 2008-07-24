from mudpyl.library.targetting import Targetter
from mudpyl.triggers import LineAlterer
from mudpyl.realms import RootRealm, TriggerMatchingRealm, AliasMatchingRealm
from mudpyl.colours import fg_code, RED
from mudpyl.metaline import Metaline, RunLengthList
import re
from mock import Mock

mobj = re.search('(foo)', 'bar foo baz')

class TestTargetting:

    def setUp(self):
        self.r = Mock(spec = RootRealm)
        self.r.macros = {}
        self.r.triggers = []
        self.r.aliases = []
        self.t = Targetter(self.r)
        self.amr = AliasMatchingRealm('foo', True, self.r, self.r, Mock())

    def test_set_target_default_regex(self):
        assert self.t.target_seen.regex is None

    def test_set_target_regex_setting(self):
        self.t.set_target.func(mobj, self.amr)
        assert self.t.target_seen.regex.pattern == r"\bfoos?'?s?\b"

    def test_set_target_sends_target_line(self):
        self.t.set_target.func(mobj, self.amr)
        argslist = [args for (args, kwargs) in self.r.send.call_args_list]
        assert argslist == [('settarget tar foo', False)]

    def test_set_target_sets_the_target_caselessly(self):
        self.t.set_target.func(mobj, self.amr)
        ml = Metaline('FOO', RunLengthList([(0, None)]), 
                             RunLengthList([(0, None)]))
        res = list(self.t.target_seen.match(ml))
        assert res, res

    def test_clear_target_nuking_regex(self):
        self.t.target_seen.regex = 'foo'
        self.t.clear_target.func(mobj, self.amr)
        assert self.t.target_seen.regex is None

    def test_clear_target_sends_clear_line(self):
        self.t.clear_target.func(mobj, self.amr)
        arglist = [args for (args, kwargs) in self.r.send.call_args_list]
        assert arglist == [('cleartarget tar', False)]

    def test_target_seen_highlighting(self):
        ml = Metaline('bar foo baz', RunLengthList([(0, 'foo')]), 
                      RunLengthList([(0, 'bar')]))
        ti = TriggerMatchingRealm(ml, self.r, self.r, Mock())
        a = ti.alterer
        self.t.target_seen.func(mobj, ti)
        res = a.apply(ml)
        assert res.fores.values[:] == [(0, 'foo'),
                                                    (4, fg_code(RED, True)),
                                                    (7, 'foo')]
