from mudpyl.library.balance import balance_highlight
from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.colours import HexFGCode
from mudpyl.triggers import LineAlterer
from mudpyl.realms import RootRealm, TriggerMatchingRealm
from mock import Mock
from mudpyl.net.telnet import TelnetClientFactory
import sys
import re

class Test_balance_highlight:

    def setUp(self):
        self.trig = balance_highlight()

    def test_matches_on_balance(self):
        assert list(self.trig.match(Metaline("You have recovered balance on "
                                             "all limbs.", None, None)))

    def test_matches_on_equilibrium(self):
        assert list(self.trig.match(Metaline("You have recovered equilibrium.",
                                             None, None)))

    def test_highlights(self):
        m = Metaline("foo", RunLengthList([(0, 'foo')]), 
                     RunLengthList([(0, 'bar')]))
        root = RootRealm(Mock(spec = TelnetClientFactory))
        realm = TriggerMatchingRealm(m, root, root)
        match = re.search('foobar', 'foobar')
        self.trig.func(match, realm)
        res = realm.alterer.apply(m)
        assert res.fores.items() == \
                [(0, HexFGCode(0x80, 0xFF, 0x80)),
                 (6, 'foo')]
