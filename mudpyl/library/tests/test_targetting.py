from mudpyl.library.targetting import Targetter
from mudpyl.triggers import LineAlterer
from mudpyl.realms import RootRealm, TriggerMatchingRealm, AliasMatchingRealm
from mudpyl.colours import fg_code, RED
from mudpyl.metaline import Metaline, RunLengthList
import re

class MockFactory:

    def __init__(self):
        self.macros = {}
        self.triggers = []
        self.aliases = []

class MockRootRealm:
    
    def __init__(self):
        self.lines_processed = []

    def send(self, line, echo = None):
        self.lines_processed.append(line)

mobj = re.search('(foo)', 'bar foo baz')

def test_set_target_default_regex():
    assert Targetter(MockFactory()).target_seen.regex is None

def test_set_target_regex_setting():
    t = Targetter(MockFactory())
    r = MockRootRealm()
    amr = AliasMatchingRealm('foo', True, r, r)
    t.set_target.func(mobj, amr)
    assert t.target_seen.regex.pattern == r"\bfoos?'?s?\b"

def test_set_target_sends_target_line():
    t = Targetter(MockFactory())
    r = MockRootRealm()
    amr = AliasMatchingRealm('foo', True, r, r)
    t.set_target.func(mobj, amr)
    assert r.lines_processed == ['settarget tar foo'], r.lines_processed

def test_set_target_sets_the_target_caselessly():
    t = Targetter(MockFactory())
    r = MockRootRealm()
    amr = AliasMatchingRealm('foo', True, r, r)
    t.set_target.func(mobj, amr)
    ml = Metaline('FOO', RunLengthList([(0, None)]), 
                         RunLengthList([(0, None)]))
    res = t.target_seen.match(ml)
    assert res, res

def test_clear_target_nuking_regex():
    t = Targetter(MockFactory())
    t.target_seen.regex = 'foo'
    r = MockRootRealm()
    amr = AliasMatchingRealm('foo', True, r, r)
    t.clear_target.func(mobj, amr)
    assert t.target_seen.regex is None

def test_clear_target_sends_clear_line():
    t = Targetter(MockFactory())
    r = MockRootRealm()
    amr = AliasMatchingRealm('foo', True, r, r)
    t.clear_target.func(mobj, amr)
    assert r.lines_processed == ['cleartarget tar'], r.lines_processed

def test_target_seen_highlighting():
    t = Targetter(MockFactory())
    r = MockRootRealm()
    ml = Metaline('bar foo baz', RunLengthList([(0, 'foo')]), 
                  RunLengthList([(0, 'bar')]))
    ti = TriggerMatchingRealm(ml, r, r)
    a = ti.alterer
    t.target_seen.func(mobj, ti)
    res = a.apply(ml)
    assert res.fores.as_pruned_index_list() == [(0, 'foo'),
                                                (4, fg_code(RED, True)),
                                                (7, 'foo')]
