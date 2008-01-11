from mudpyl.net.telnet import TelnetClientFactory

def test_TelnetClientFactory_sets_name():
    o = object()
    c = TelnetClientFactory(o)
    assert c.name is o

from mudpyl.net.telnet import TelnetClient
from mudpyl.net.mccp import COMPRESS2

class Test_LineReceiver_aspects:

    def setUp(self):
        self.received = []
        self.tc = TelnetClient(TelnetClientFactory(None))
        self.tc.transport = FakeTransport()
        self.tc.lineReceived = self.lr

    def lr(self, line):
        self.received.append(line)

    def test_boring(self):
        self.tc.dataReceived("foo\r\nbar\r\nbaz")
        assert self.received == ['foo', 'bar'], self.received

    def test_closing_flushes_buffer(self):
        self.tc.dataReceived("bar")
        print self.tc.factory.outputs
        self.tc.connectionLost(None)
        assert self.received == ['bar']

class Test_sending_lines:

    def setUp(self):
        self.tc = TelnetClient(None)
        self.tc.transport = self.transport = FakeTransport()

    def test_sendLine_appends_crlf(self):
        self.tc.sendLine("foo")
        assert self.transport.written == 'foo\r\n'

class FakeTransport:
    def __init__(self):
        self.their_mccp_active = False
        self.lost_connection = False
        self.written = ''

    def writeSequence(self, seq):
        self.written += ''.join(seq)

    def loseConnection(self):
        self.lost_connection = True

    disconnecting = False

class Test_MCCP:

    def setUp(self):
        self.tc = TelnetClient(TelnetClientFactory(None))
        self.tc.transport = self.t = FakeTransport()

    def test_agree_to_enable_COMPRESS2(self):
        assert self.tc.enableRemote(COMPRESS2)

    def test_doesnt_agree_to_random_nexed_options(self):
        assert not self.tc.enableRemote('\xA2')

    def test_doesnt_enable_MCCP_without_COMPRESS2(self):
        self.tc.negotiationMap[COMPRESS2]('')
        assert not self.t.their_mccp_active

    def test_does_enable_MCCP_with_COMPRESS2(self):
        self.tc.enableRemote(COMPRESS2)
        self.tc.negotiationMap[COMPRESS2]('')
        assert self.t.their_mccp_active

    def test_enable_disable_leaves_disabled(self):
        self.tc.enableRemote(COMPRESS2)
        self.tc.disableRemote(COMPRESS2)
        self.tc.negotiationMap[COMPRESS2]('')
        assert not self.t.their_mccp_active

    def test_close_loses_connection(self):
        self.tc.close()
        assert self.t.lost_connection

class FakeRealmWithSoftGAs:

    def __init__(self):
        self.lines = []
        self.ga_as_line_end = True

    def receive(self, line):
        self.lines.append(line)

from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.colours import fg_code, RED, WHITE, BLACK, bg_code
from twisted.conch.telnet import IAC, GA, BS, VT

class Test_receiving_lines:

    def setUp(self):
        f = TelnetClientFactory(None)
        f.realm = self.e = FakeRealmWithSoftGAs()
        self.tc = TelnetClient(f)
        self.tc.transport = FakeTransport()
        self.fores = RunLengthList([(0, fg_code(WHITE, False))])
        self.backs = RunLengthList([(0, bg_code(BLACK))])

    def test_ga_received_sends_line_on(self):
        expected = [Metaline('foo', self.fores, self.backs, wrap = True,
                             line_end = 'soft')]
        self.tc.dataReceived("foo" + IAC + GA)
        print expected
        assert self.e.lines == expected, self.e.lines

    def test_ga_received_flushes_out_the_buffer(self):
        expected = [Metaline("foo", self.fores, self.backs, wrap = True,
                             line_end = 'soft'),
                    Metaline('', self.fores, self.backs, wrap = True,
                             line_end = 'soft')]
        self.tc.dataReceived('foo' + IAC + GA + IAC + GA)
        assert self.e.lines == expected, self.e.lines

    def test_ga_received_respects_ga_as_line_end_flag(self):
        self.e.ga_as_line_end = False
        expected = [Metaline('foo', self.fores, self.backs, wrap = True,
                             line_end = None)]
        self.tc.dataReceived("foo" + IAC + GA)
        assert self.e.lines == expected, self.e.lines

    def test_lineReceived_sends_line_on(self):
        self.tc.lineReceived("foo")
        assert self.e.lines == [Metaline('foo', self.fores, self.backs, 
                                         wrap = True)]

    def test_lineReceived_parses_colours(self):
        expected = [Metaline('foo', RunLengthList([(0, fg_code(RED, False))]),
                             self.backs, wrap = True)]
        self.tc.lineReceived('\x1b[31mfoo')
        assert self.e.lines == expected
    
    def test_lineReceived_works_via_dataReceived(self):
        expected = [Metaline('foo', self.fores, self.backs, wrap = True)]
        self.tc.dataReceived('foo\r\n')
        assert self.e.lines == expected

    def test_lineReceived_cleans_out_VT100_stuff(self):
        expected = [Metaline('foo', self.fores, self.backs, wrap = True)]
        self.tc.lineReceived('fooQ' + BS + VT)
        assert self.e.lines == expected

class MockOutputManager:

    def __init__(self):
        self.calls = []

    def connection_opened(self):
        self.calls.append("connection_opened")

    def connection_closed(self):
        self.calls.append("connection_closed")

def test_connectionLost_sends_connection_closed_to_the_outputs():
    f = TelnetClientFactory(None)
    telnet = TelnetClient(f)
    om = f.outputs = MockOutputManager()

    telnet.connectionLost(None)

    assert om.calls == ['connection_closed']

def test_connectionMade_sends_connection_opened_to_the_outputs():
    f = TelnetClientFactory(None)
    telnet = TelnetClient(f)
    om = f.outputs = MockOutputManager()

    telnet.connectionMade()

    assert om.calls == ['connection_opened']
