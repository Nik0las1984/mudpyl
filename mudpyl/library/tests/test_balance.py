from mudpyl.library.balance import balance_highlight
from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.colours import HexFGCode
from mudpyl.triggers import LineAlterer
from mudpyl.realms import RootRealm, TriggerMatchingRealm
import sys
import re

class FakeTelnet:

    def __init__(self):
        self.sent = []

    def sendLine(self, line):
        self.sent.append(line)

class FakeOutputManager:

    def __init__(self):
        self.fore = object()
        self.back = object()
        self.written = []

    def write_to_screen(self, metaline):
        self.written.append(metaline)

class FakeFactory:

    def __init__(self):
        self.outputs = FakeOutputManager()

class Test_balance_highlight:

    def setUp(self):
        self.trig = balance_highlight()

    def test_matches_on_balance(self):
        assert self.trig.match(Metaline("You have recovered balance on all "
                                        "limbs.", None, None))

    def test_matches_on_equilibrium(self):
        assert self.trig.match(Metaline("You have recovered equilibrium.",
                                        None, None))

    def test_highlights(self):
        m = Metaline("foo", RunLengthList([(0, 'foo')]), 
                     RunLengthList([(0, 'bar')]))
        root = RootRealm(FakeFactory())
        realm = TriggerMatchingRealm(m, root, root)
        match = re.search('foobar', 'foobar')
        self.trig.func(match, realm)
        res = realm.alterer.apply(m)
        assert res.fores.as_pruned_index_list() == \
                [(0, HexFGCode(0x80, 0xFF, 0x80)),
                 (6, 'foo')]
