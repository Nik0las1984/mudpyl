"""Implements MCCP, the Mud Client Compression Protocol.

See http://mccp.afkmud.com/protocol.html for the official definition.
"""
from twisted.internet.protocol import Protocol, connectionDone
from twisted.conch.telnet import IAC, SE, ProtocolTransportMixin
import zlib

#we don't even make an effort to support COMPRESS (v1 of the protocol)
#because of the pain that parsing unterminated subnegotiation sequences would
#cause. MUD owners: if you want to save bandwidth, switch to COMPRESS2!
COMPRESS2 = chr(86)

class MCCPTransport(Protocol, ProtocolTransportMixin):
    """A transport-cum-protocol that (sort of) invisibly handles MCCP."""
    
    def __init__(self, protocol):
        self.their_mccp_active = False
        self.our_mccp_active = False
        self.later = ''
        self.decompressor = zlib.decompressobj()
        self.protocol = protocol

    @property
    def disconnecting(self):
        """Dunno what this is for, but some stuff needs a Transport to have
        this attribute.
        """
        return self.transport.disconnecting
    
    #pylint doesn't like Twisted naming conventions
    #pylint: disable-msg= C0103

    def connectionMade(self):
        """A connection's been made. Inform our protocol."""
        self.protocol.makeConnection(self)

    def connectionLost(self, reason = connectionDone):
        """We've lost the connection. Inform our protocol."""
        #make sure nothing's trapped in our buffers
        if self.their_mccp_active:
            #this can occur if the last thing the MUD sent was compressed with
            #Z_FINISH as an option. Dunno what's so special about that that
            #needs it kept in an internal buffer of decompressobj, but that's
            #how it is.
            self.protocol.dataReceived(self.decompressor.flush())
        else:
            #This primarily occurs when self.later is just an IAC. In fact, I
            #think that's the only condition that can lead to this.
            self.protocol.dataReceived(self.later)
        self.protocol.connectionLost(reason)

    def dataReceived(self, data):
        """We've received some data. Process it."""
        self.later += data
        self._process()

    def _process(self):
        """Depending on whether MCCP is active or not, this method does two
        things:

          - If it is not active, it breaks the received data into sections,
            where each break occurs where COMPRESS2 could reasonably be turned
            on.
          - If compression is on, then the input is decoded.
        """
        while self.later:
            if not self.their_mccp_active:
            	#We need to break at IAC SE, because COMPRESS2 is activated by
            	#a subnegotiation sequence. To see why we need to split it
            	#here, consider this text sequence:
            	# 'foo' + IAC + SB + COMPRESS2 + IAC + SE + compress('bar')
            	#If we don't split our input up at IAC SEs, then the second,
            	#compressed, part of the string will be treated as not being
            	#compressed. This manifests itself as a unicode decoding error
            	#amongst other things, but that's only a symptom.
                first, sep, self.later = self.later.partition(IAC + SE)
                #stop chopped IAC SE sequences being, well, chopped.
                if not sep and first.endswith(IAC):
                    self.later = IAC + self.later
                    first = first[:-1]
                self.protocol.dataReceived(first + sep)
                if not sep:
                    #need to break out here, else we'll loop infinitely when
                    #we've re-atomicised a chopped sequence.
                    break
            else:
                first = self.decompressor.decompress(self.later)
                #extract the data past the end of this particular compressed
                #string.
                self.later = self.decompressor.unused_data
                if self.later:
                    #the MUD has ended the decompression. We've got a leftover
                    #bit of uncompressed data here still.
                    self.decompressor = zlib.decompressobj()
                    self.their_mccp_active = False
                if first:
                    self.protocol.dataReceived(first)
