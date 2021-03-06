from mudpyl.library.colourtells import TellColourer
from mudpyl.metaline import RunLengthList, Metaline, simpleml
from mudpyl.net.telnet import TelnetClientFactory, TelnetClient
from mudpyl.colours import WHITE, BLACK, fg_code, bg_code
from mock import Mock

class Test_TellColourer:

    def setUp(self):
        self.fact = TelnetClientFactory(None, 'ascii', None)
        self.p = Mock()
        self.fact.realm.addProtocol(self.p)
        self.fact.realm.telnet = Mock(spec = TelnetClient)
        self.tc = TellColourer(self.fact.realm)

    def test_adds_aliases(self):
        assert self.tc.sending_tell in self.fact.realm.aliases

    def test_adds_triggers(self):
        assert self.tc.tell_sent in self.fact.realm.triggers
        assert self.tc.no_tell_sent in self.fact.realm.triggers
        assert self.tc.tell_received in self.fact.realm.triggers

    def test_tell_received_matches_on_tells_in_languages(self):
        ml = Metaline('Foo tells you in Foolang, "Bar."',
                      None, None)
        assert list(self.tc.tell_received.match(ml))

    def test_tell_sent_matches_on_tells_in_languages(self):
        ml = Metaline('You tell Mister Foo in Barlang, "Qux."',
                      None, None)
        assert list(self.tc.tell_sent.match(ml))

    def test_tell_sent_pattern_is_not_greedy(self):
        ml = Metaline('You tell Foo, "Bar, "baz.""', None, None)
        match = list(self.tc.tell_sent.match(ml))
        assert match[0].group(1) == 'Foo'

    def test_no_tell_sent_doesnt_cock_up(self):
        ml = simpleml('Bar tells you, "Blah."', fg_code(WHITE, False),
                      bg_code(BLACK))
        self.fact.realm.metalineReceived(ml)
        ml_written = self.p.metalineReceived.call_args[0][0]
        colour_expecting = ml_written.fores.get_at(0)

        self.fact.realm.send("tell baz blah")
        ml = simpleml("Whom do you wish to tell to?", fg_code(WHITE, False),
                      bg_code(BLACK))
        self.fact.realm.metalineReceived(ml)

        self.fact.realm.send("tell bar blah")
        ml = simpleml('You tell Bar, "Blah."', fg_code(WHITE, False),
                      bg_code(BLACK))
        self.fact.realm.metalineReceived(ml)
        ml_written_2 = self.p.metalineReceived.call_args[0][0]

        assert ml_written_2.fores.get_at(10) == colour_expecting

    def test_tell_sending_alias_is_caseless_wrt_matching(self):
        assert list(self.tc.sending_tell.match("TELL foo bar"))

    #XXX
