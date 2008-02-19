from mudpyl.library.general import repeat
from mudpyl.aliases import AliasMatchingRealm
from mock import Mock
import re

class Test_RepeatAlias:

    def setUp(self):
        self.a = repeat()
        self.i = Mock(spec = AliasMatchingRealm)
        self.i.send_to_mud = True

    def test_doesnt_send_original_to_mud(self):
        m = re.search('(0)(foo)', '0foo')
        self.a.func(m, self.i)
        assert not self.i.send_to_mud

    def test_sends_n_times(self):
        m = re.search('(10)(foo)', '10foo')
        self.a.func(m, self.i)
        assert len(self.i.send.call_args_list) == 10

    def test_sends_same_thing_each_time(self):
        m = re.search("(10)(foo)", "10foo")
        self.a.func(m, self.i)
        assert all((args == ('foo',))
                   for (args, kwargs) in self.i.send.call_args_list)
