from mudpyl.net.telnet import TelnetClientFactory
from mock import Mock
from mudpyl.realms import RootRealm

def test_TelnetClientFactory_sets_name():
    o = object()
    c = TelnetClientFactory(o, None, None)
    assert c.name is o

def test_TelnetClientFactory_sets_encoding():
    o = object()
    c = TelnetClientFactory(None, o, None)
    assert c.encoding is o

def test_TelnetclientFactory_sets_main_module_name():
    o = object()
    c = TelnetClientFactory(None, None, o)
    assert c.main_module_name is o

from mudpyl.net.telnet import TelnetClient
from mudpyl.net.mccp import COMPRESS2

class Test_LineReceiver_aspects:

    def setUp(self):
        self.received = []
        self.tc = TelnetClient(TelnetClientFactory(None, 'ascii', None))
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
        self.f = TelnetClientFactory(None, 'ascii', None)
        self.tc = TelnetClient(self.f)
        self.tc.transport = self.transport = FakeTransport()

    def test_sendLine_appends_crlf(self):
        self.tc.sendLine("foo")
        assert self.transport.written == 'foo\r\n'

    def test_doubles_IAC(self):
        self.f.encoding = 'cp1250'
        #crock a unicode sequence that has 0xFF in it as CP1250
        self.tc.sendLine(u'foo\u02D9bar')
        assert self.transport.written == 'foo\xff\xffbar\r\n'

    def test_with_interesting_encoding(self):
        self.f.encoding = 'utf-8'
        self.tc.sendLine(u'foo')
        assert self.transport.written == 'foo\r\n'

    def test_with_interesting_encoding_and_interesting_characters(self):
        self.f.encoding = 'cp1250'
        self.tc.sendLine(u'foo\u2019bar')
        assert self.transport.written == 'foo\x92bar\r\n'

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
        self.tc = TelnetClient(TelnetClientFactory(None, 'ascii', None))
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

from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.colours import fg_code, RED, WHITE, BLACK, bg_code
from twisted.conch.telnet import IAC, GA, BS, VT

class Test_receiving_lines:

    def setUp(self):
        self.f = TelnetClientFactory(None, 'ascii', None)
        self.f.realm = self.e = Mock(spec = RootRealm)
        self.e.ga_as_line_end = True
        self.tc = TelnetClient(self.f)
        self.tc.transport = FakeTransport()
        self.fores = RunLengthList([(0, fg_code(WHITE, False))])
        self.backs = RunLengthList([(0, bg_code(BLACK))])

    def test_ga_received_sends_line_on(self):
        expected = [Metaline('foo', self.fores, self.backs, wrap = True,
                             line_end = 'soft')]
        self.tc.dataReceived("foo" + IAC + GA)
        print expected
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == expected, lines

    def test_ga_received_flushes_out_the_buffer(self):
        expected = [Metaline("foo", self.fores, self.backs, wrap = True,
                             line_end = 'soft'),
                    Metaline('', self.fores, self.backs, wrap = True,
                             line_end = 'soft')]
        self.tc.dataReceived('foo' + IAC + GA + IAC + GA)
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == expected, lines

    def test_ga_received_respects_ga_as_line_end_flag(self):
        self.e.ga_as_line_end = False
        expected = [Metaline('foo', self.fores, self.backs, wrap = True,
                             line_end = None)]
        self.tc.dataReceived("foo" + IAC + GA)
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == expected, lines

    def test_lineReceived_sends_line_on(self):
        self.tc.lineReceived("foo")
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == [Metaline('foo', self.fores, self.backs, wrap = True)]

    def test_lineReceived_parses_colours(self):
        expected = [Metaline('foo', RunLengthList([(0, fg_code(RED, False))]),
                             self.backs, wrap = True)]
        self.tc.lineReceived('\x1b[31mfoo')
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == expected, lines

    def test_lineReceived_works_via_dataReceived(self):
        expected = [Metaline('foo', self.fores, self.backs, wrap = True)]
        self.tc.dataReceived('foo\r\n')
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == expected, lines

    def test_lineReceived_cleans_out_VT100_stuff(self):
        expected = [Metaline('foo', self.fores, self.backs, wrap = True)]
        self.tc.lineReceived('fooQ' + BS + VT)
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == expected, lines

    def test_lineReceived_decodes_data(self):
        #real-ish example that booted me :(
        self.f.encoding = 'cp1250'
        expected = [Metaline(u"bar\u2019baz", self.fores, self.backs, 
                             wrap = True)]
        self.tc.lineReceived('bar\x92baz')
        lines = [line for ((line,), kwargs) in self.e.receive.call_args_list]
        assert lines == expected, lines

def test_connectionLost_sends_connection_closed_to_the_outputs():
    f = TelnetClientFactory(None, 'ascii', None)
    telnet = TelnetClient(f)
    r = f.realm = Mock(spec = RootRealm)

    telnet.connectionLost(None)

    assert r.connection_lost.called

def test_connectionMade_sends_connection_opened_to_the_outputs():
    f = TelnetClientFactory(None, 'ascii', None)
    telnet = TelnetClient(f)
    r = f.realm = Mock(spec = RootRealm)

    telnet.connectionMade()

    assert r.connection_made.called
