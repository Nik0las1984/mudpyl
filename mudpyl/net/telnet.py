"""The actual connection to the MUD."""
from twisted.conch.telnet import Telnet, GA, IAC, ECHO
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ClientFactory
from mudpyl.net.nvt import ColourCodeParser, make_string_sane
from mudpyl.net.mccp import MCCPTransport, COMPRESS2
from mudpyl.realms import RootRealm
import re

broken_line_ending_pattern = re.compile("([^\r]|^)\n\r")

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
        self.fix_broken_godwars_line_endings = True

    def connectionMade(self):
        """Call our superclasses.
        
        Late initialisation should also go here.
        """
        self.factory.realm.connectionMade()
        Telnet.connectionMade(self)
        LineOnlyReceiver.connectionMade(self)

    def enableRemote(self, option):
        """Allow MCCP to be turned on."""
        if option == COMPRESS2:
            self.allowing_compress = True
            return True
        elif option == ECHO:
            self.factory.realm.server_echo = True
            #hide the command line
            self.factory.gui.command_line.set_visibility(False)
            return True
        else:
            return False

    def disableRemote(self, option):
        """Allow MCCP to be turned off."""
        if option == COMPRESS2:
            self.allowing_compress = False
        elif option == ECHO:
            self.factory.realm.server_echo = False
            self.factory.gui.command_line.set_visibility(True)

    def turn_on_compression(self, bytes):
        """Actually enable MCCP."""
        #invalid states.   
        if not self.allowing_compress or bytes:
            return
        self.transport.their_mccp_active = True

    def dataReceived(self, data):
        if self.fix_broken_godwars_line_endings:
            while broken_line_ending_pattern.match(data):
                data = re.sub(broken_line_ending_pattern, "\\1\r\n", data, 1)
        Telnet.dataReceived(self, data)

    applicationDataReceived = LineOnlyReceiver.dataReceived

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
        self.factory.realm.connectionLost()

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
            metaline.line_end = 'soft'
        else:
            metaline.line_end = 'hard'
        metaline.wrap = True
        self.factory.realm.metalineReceived(metaline)

class TelnetClientFactory(ClientFactory):

    """A ClientFactory that produces TelnetClients."""

    def __init__(self, name, encoding, main_module_name):
        #no __init__ here, either.
        self.name = name
        self.encoding = encoding
        self.main_module_name = main_module_name
        self.realm = RootRealm(self)

    protocol = TelnetClient

    def buildProtocol(self, addr):
        """Build our protocol's instance."""
        prot = self.protocol(self)
        self.realm.telnet = prot
        mccp = MCCPTransport(prot)
        return mccp
