from mudpyl.library.colourtells import TellColourer
from mudpyl.metaline import RunLengthList, Metaline
from mudpyl.net.telnet import TelnetClientFactory
from mudpyl.realms import RootRealm

class FakeOutputs:

    def __init__(self):
        self.wtsed = []

    def write_to_screen(self, metaline):
        self.wtsed.append(metaline)

class StubTelnet:

    def sendLine(self, line):
        pass

class Test_TellColourer:

    def setUp(self):
        self.fact = TelnetClientFactory(None, 'ascii')
        self.fact.outputs = FakeOutputs()
        self.fact.realm.telnet = StubTelnet()
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
        assert self.tc.tell_received.match(ml)

    def test_tell_sent_matches_on_tells_in_languages(self):
        ml = Metaline('You tell Mister Foo in Barlang, "Qux."',
                      None, None)
        assert self.tc.tell_sent.match(ml)

    def test_tell_sent_pattern_is_not_greedy(self):
        ml = Metaline('You tell Foo, "Bar, "baz.""', None, None)
        match = self.tc.tell_sent.match(ml)
        assert match[0].group(1) == 'Foo'

    def test_no_tell_sent_doesnt_cock_up(self):
        ml = Metaline('Bar tells you, "Blah."', RunLengthList([(0, None)]), 
                      RunLengthList([(0, None)]))
        self.fact.realm.receive(ml)
        ml_written = self.fact.outputs.wtsed[0]
        colour_expecting = ml_written.fores.as_populated_list()[0]

        self.fact.realm.send("tell baz blah")
        ml = Metaline("Whom do you wish to tell to?", 
                      RunLengthList([(0, None)]),
                      RunLengthList([(0, None)]))
        self.fact.realm.receive(ml)

        self.fact.realm.send("tell bar blah")
        ml = Metaline('You tell Bar, "Blah."', RunLengthList([(0, None)]),
                      RunLengthList([(0, None)]))
        self.fact.realm.receive(ml)
        ml_written_2 = self.fact.outputs.wtsed[4]

        print ml_written_2, '\n'.join(str(o) for o in self.fact.outputs.wtsed)
        assert ml_written_2.fores.as_populated_list()[9] == colour_expecting

    def test_tell_sending_alias_is_caseless_wrt_matching(self):
        assert self.tc.sending_tell.match("TELL foo bar")

    #XXX
