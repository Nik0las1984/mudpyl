from mudpyl.library.imperian.balance import balance_highlight
from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.colours import HexFGCode
from mudpyl.triggers import LineAlterer
from mudpyl.realms import RootRealm, TriggerMatchingRealm
from mudpyl.net.telnet import TelnetClientFactory
from mock import Mock
import re

class Test_balance_highlight:

    def setUp(self):
        self.trig = balance_highlight()

    def test_matches_on_balance(self):
        assert list(self.trig.match(Metaline("You have recovered balance.",
                                             None, None)))

    def test_highlights(self):
        m = Metaline("foo", RunLengthList([(0, 'foo')]), 
                     RunLengthList([(0, 'bar')]))
        root = RootRealm(TelnetClientFactory(None, None, None))
        realm = TriggerMatchingRealm(m, root, root, Mock())
        match = re.search('foobar', 'foobar')
        self.trig.func(match, realm)
        res = realm.alterer.apply(m)
        assert res.fores.values[:] == \
                [(0, HexFGCode(0x80, 0xFF, 0x80)),
                 (6, 'foo')]
