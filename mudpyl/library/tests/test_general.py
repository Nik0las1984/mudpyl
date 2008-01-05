from mudpyl.library.general import repeat
from mudpyl.realms import AliasMatchingRealm
import re

class MockRealm:

    def send(self, line, echo):
        pass

class Test_RepeatAlias:

    def setUp(self):
        self.a = repeat()
        self.r = MockRealm()
        self.i = AliasMatchingRealm('0foo', None, self.r, self.r)

    def test_doesnt_send_to_mud(self):
        m = re.search('(0)(foo)', '0foo')
        self.a.func(m, self.i)
        assert not self.i.send_to_mud
