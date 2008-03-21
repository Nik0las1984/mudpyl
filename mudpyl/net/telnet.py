"""The actual connection to the MUD."""
from twisted.conch.telnet import Telnet, GA, IAC, NOP, DM, BRK, IP, AO, AYT, \
                                 EC, EL, WILL, WONT, DO, DONT, SB, SE
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ClientFactory
from mudpyl.net.nvt import ColourCodeParser, make_string_sane
from mudpyl.output_manager import OutputManager
from mudpyl.net.mccp import MCCPTransport, COMPRESS2
from mudpyl.realms import RootRealm

#pylint doesn't like Twisted naming conventions
#pylint: disable-msg= C0103

class TelnetClient(Telnet, LineOnlyReceiver):

    """The link to the MUD."""

    delimiter = '\n'

    def __init__(self, factory):
        Telnet.__init__(self)
        self.commandMap[GA] = self.ga_received
        self.negotiationMap[COMPRESS2] = self.turn_on_compression
        #LineOnlyReceiver doesn't have an __init__ method, weirdly.
        self.factory = factory
        self.allowing_compress = False
        self._colourparser = ColourCodeParser()

    def connectionMade(self):
        """Call our superclasses.
        
        Late initialisation should also go here.
        """
        self.factory.realm.connection_made()
        Telnet.connectionMade(self)
        LineOnlyReceiver.connectionMade(self)

    def enableRemote(self, option):
        """Allow MCCP to be turned on."""
        if option == COMPRESS2:
            self.allowing_compress = True
            return True
        else:
            return False

    def disableRemote(self, option):
        """Allow MCCP to be turned off."""
        if option == COMPRESS2:
            self.allowing_compress = False

    def turn_on_compression(self, bytes):
        """Actually enable MCCP."""
        #invalid states.   
        if not self.allowing_compress or bytes:
            return
        self.transport.their_mccp_active = True

    applicationDataReceived = LineOnlyReceiver.dataReceived

    def dataReceived(self, data):
        """Receive some data from the MUD's server.

        This function is lifted from Twisted's trunk, for efficiency, and is
        thus copyright whoever wrote it and under whatever license it's
        under.
        """
        appDataBuffer = []

        for b in data:
            if self.state == 'data':
                if b == IAC:
                    self.state = 'escaped'
                elif b == '\r':
                    self.state = 'newline'
                else:
                    appDataBuffer.append(b)
            elif self.state == 'escaped':
                if b == IAC:
                    appDataBuffer.append(b)
                    self.state = 'data'
                elif b == SB:
                    self.state = 'subnegotiation'
                    self.commands = []
                elif b in (NOP, DM, BRK, IP, AO, AYT, EC, EL, GA):
                    self.state = 'data'
                    if appDataBuffer:
                        self.applicationDataReceived(''.join(appDataBuffer))
                        del appDataBuffer[:]
                    self.commandReceived(b, None)
                elif b in (WILL, WONT, DO, DONT):
                    self.state = 'command'
                    self.command = b
                else:
                    raise ValueError("Stumped", b)
            elif self.state == 'command':
                self.state = 'data'
                command = self.command
                del self.command
                if appDataBuffer:
                    self.applicationDataReceived(''.join(appDataBuffer))
                    del appDataBuffer[:]
                self.commandReceived(command, b)
            elif self.state == 'newline':
                if b == '\n':
                    appDataBuffer.append('\n')
                elif b == '\0':
                    appDataBuffer.append('\r')
                else:
                    appDataBuffer.append('\r' + b)
                self.state = 'data'
            elif self.state == 'subnegotiation':
                if b == IAC:
                    self.state = 'subnegotiation-escaped'
                else:
                    self.commands.append(b)
            elif self.state == 'subnegotiation-escaped':
                if b == SE:
                    self.state = 'data'
                    commands = self.commands
                    del self.commands
                    if appDataBuffer:
                        self.applicationDataReceived(''.join(appDataBuffer))
                        del appDataBuffer[:]
                    self.negotiate(commands)
                else:
                    self.state = 'subnegotiation'
                    self.commands.append(b)
            else:
                raise ValueError("How'd you do this?")

        if appDataBuffer:
            self.applicationDataReceived(''.join(appDataBuffer))

    def close(self):
        """Convenience: close the connection."""
        self.transport.loseConnection()

    def sendLine(self, line):
        """Send a line plus a line delimiter to the MUD.

        We need to override this because Telnet converts \\r\\n -> \\n, so
        LineReceiver's delimiter needs to be \\n, but we need to -send- lines
        terminated by \\r\\n. Sigh.
        """
        line = line.encode(self.factory.encoding)
        #double IAC, else it might be interpreted as a command
        line = line.replace(IAC, IAC + IAC)
        return self.transport.writeSequence([line, '\r\n'])

    def connectionLost(self, reason):
        """Clean up and let the superclass handle it."""
        Telnet.connectionLost(self, reason)
        LineOnlyReceiver.connectionLost(self, reason)
        #flush out the buffer
        if self._buffer:
            self.lineReceived(self._buffer)
        self.factory.realm.connection_lost()

    def ga_received(self, _):
        """A GA's been received. We treat these kind of like line endings."""
        #uses the internals of LineOnyReceiver
        self._handle_line(self._buffer, from_ga = True)
        self._buffer = ''

    def lineReceived(self, line):
        """A normally terminated line's been received from the MUD."""
        self._handle_line(line, from_ga = False)

    def _handle_line(self, line, from_ga):
        """Clean the line, split out the colour codes, and feed it to the 
        realm as a metaline.
        """
        line = line.decode(self.factory.encoding)
        metaline = self._colourparser.parseline(make_string_sane(line))
        if from_ga:
            if self.factory.realm.ga_as_line_end:
                metaline.line_end = 'soft'
            else:
                metaline.line_end = None
        else:
            metaline.line_end = 'hard'
        metaline.wrap = True
        self.factory.realm.receive(metaline)

class TelnetClientFactory(ClientFactory):

    """A ClientFactory that produces TelnetClients."""

    def __init__(self, name, encoding, main_module_name):
        #no __init__ here, either.
        self.name = name
        self.encoding = encoding
        self.main_module_name = main_module_name
        self.outputs = OutputManager(self)
        self.realm = RootRealm(self)

    protocol = TelnetClient

    def buildProtocol(self, addr):
        """Build our protocol's instance."""
        prot = self.protocol(self)
        self.realm.telnet = prot
        mccp = MCCPTransport(prot)
        return mccp
