from mudpyl.net.mccp import MCCPTransport
from twisted.internet.protocol import Protocol
from twisted.conch.telnet import IAC, SE
from zlib import compress, Z_FINISH

class MockProtocol(Protocol):
    
    def __init__(self):
        self.data_received = ''
        self.connection_lost = False
        self.reason = None

    def dataReceived(self, data):
        self.data_received += data

    def connectionLost(self, reason):
        self.connection_lost = True
        self.reason = reason

class MockProtocolWithToggle(Protocol):

    def __init__(self):
        self.data_received = ''

    def dataReceived(self, data):
        self.data_received += data
        if data.endswith(IAC + SE):
            self.transport.their_mccp_active = True

def test_toggling_decompression():
    t = MCCPTransport(MockProtocolWithToggle())
    t.connectionMade()
    p = t.protocol

    t.dataReceived('foo' + IAC + SE + compress("bar"))
    assert p.data_received == 'foo' + IAC + SE + 'bar', repr(p.data_received)

class TestMCCPTransport:

    def setUp(self):
        self.t = MCCPTransport(MockProtocol())
        self.t.connectionMade()
        self.p = self.t.protocol

    def test_passes_through_with_no_alteration(self):
        self.t.dataReceived("foo")
        assert self.p.data_received == 'foo', repr(self.p.data_received)

    def test_IAC_SE_passes_through_unaltered(self):
        self.t.dataReceived("foo" + IAC + SE + "bar")
        assert self.p.data_received == 'foo' + IAC + SE + 'bar', \
               repr(self.p.data_received)

    def test_chopped_IAC_SE_works(self):
        self.t.dataReceived('foo' + IAC)
        assert self.p.data_received == 'foo', self.p.data_received

    def test_chopped_IAC_SE_completion(self):
        self.t.dataReceived('foo' + IAC)
        self.t.dataReceived(SE + 'bar')
        assert self.p.data_received == 'foo' + IAC + SE + 'bar', \
               self.p.data_received

    def test_decompresses_normal_text(self):
        self.t.their_mccp_active = True
        self.t.dataReceived(compress("foo"))
        assert self.p.data_received == 'foo', repr(self.p.data_received)

    def test_decompression_with_an_IAC_SE(self):
        self.t.their_mccp_active = True
        self.t.dataReceived(compress("foo" + IAC + SE + "bar"))
        assert self.p.data_received == 'foo' + IAC + SE + 'bar', \
               repr(self.p.data_received)

    def test_chopped_compressed_string(self):
        self.t.their_mccp_active = True
        s = compress("foo")
        self.t.dataReceived(s[:2])
        assert self.p.data_received == '', repr(self.p.data_received)

    def test_chopped_with_second_bit_of_string(self):
        self.t.their_mccp_active = True
        s = compress("foo")
        self.t.dataReceived(s[:2])
        self.t.dataReceived(s[2:])
        assert self.p.data_received == 'foo', repr(self.p.data_received)

    def test_compression_ends(self):
        self.t.their_mccp_active = True
        self.t.dataReceived(compress("foo", Z_FINISH))
        assert self.p.data_received == 'foo', repr(self.p.data_received)

    def test_compression_ends_plus_uncompressed_text(self):
        self.t.their_mccp_active = True
        self.t.dataReceived(compress("foo", Z_FINISH) + 'bar')
        assert self.p.data_received == 'foobar'
        assert not self.t.their_mccp_active

    def test_simulated_finality_compression(self):
        self.t.their_mccp_active = True
        self.t.dataReceived(compress("foo", Z_FINISH))
        self.t.connectionLost(None)
        assert self.p.connection_lost
        assert self.p.data_received == 'foo', self.p.data_received

    def test_simulated_finality_no_compression_no_IAC(self):
        self.t.dataReceived('foo')
        self.t.connectionLost(None)
        assert self.p.data_received == 'foo'

    def test_simulated_finality_with_IAC(self):
        self.t.dataReceived("foo" + IAC + SE)
        self.t.connectionLost(None)
        assert self.p.data_received == 'foo' + IAC + SE

    def test_simulated_finality_with_chopped_IAC(self):
        self.t.dataReceived("foo" + IAC)
        self.t.connectionLost(None)
        assert self.p.data_received == 'foo' + IAC
