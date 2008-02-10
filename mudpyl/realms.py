"""Hierarchical stacking contexts for execution."""
from code import InteractiveConsole
from mudpyl.escape_parser import EscapeParser
from mudpyl.colours import fg_code, bg_code, BLACK, WHITE, HexFGCode
from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.triggers import TriggerMatchingRealm
from mudpyl.aliases import AliasMatchingRealm
from mudpyl.modules import load_file
from mudpyl.gui.bindings import gui_macros
import traceback
import time

class RootRealm(object):
    """The root of the realms hierarchy. This is what macros and top-level
    modules deal with.
    """

    def __init__(self, factory):
        self.factory = factory
        self.telnet = None
        self.triggers = []
        self.aliases = []
        self.baked_in_macros = gui_macros.copy()
        self.macros = self.baked_in_macros.copy()
        self.ga_as_line_end = True
        self.modules_loaded = set()
        self._escape_parser = EscapeParser()
        self.tracing = False
        self.console_ns = {'realm': self}
        self.console = InteractiveConsole(self.console_ns)

        self.connection_event_receivers = []
        self.peeking_receivers = []
        self._closing_down = False

    #Bidirectional, or just ambivalent, functions.

    def clear_modules(self):
        """Restore our state to a pristine (ie, blank) condition.
        """
        #keep in place so references to these still work
        self.triggers[:] = []
        self.aliases[:] = []
        self.macros.clear()
        self.macros.update(self.baked_in_macros)
        self.modules_loaded = set()

    def reload_main_module(self):
        """Clear ourselves into a pristine state and load the main module
        again.
        """
        self.clear_modules()
        cls = load_file(self.factory.main_module_name)
        self.load_module(cls)

    def load_module(self, cls, _sort = True):
        """Load the triggers, aliases, macros and other modules of the given
        module.
        """
        if cls in self.modules_loaded:
            return
        #add now, so that we can avoid circular dependencies
        self.modules_loaded.add(cls)
        try:
            robmod = cls(self)
            for mod in robmod.modules:
                self.load_module(mod, _sort = False)
            if _sort:
                self.triggers.sort()
                self.aliases.sort()
        except:
            self.modules_loaded.remove(cls)
            raise
        return robmod

    def close(self):
        """Close up our connection and shut up shop.
        
        It is guaranteed that, on registered connection event receivers,
        connection_lost will be called before close.
        """
        if self.telnet is not None:
            #lose the connection first.
            self.telnet.close()
        else:
            #connection's already lost, we don't need to wait
            for receiver in self.connection_event_receivers:
                receiver.close()
        self.telnet = None
        self._closing_down = True

    def add_connection_receiver(self, receiver):
        """Register a receiver for close, connection_made and connection_lost
        events.
        """
        self.connection_event_receivers.append(receiver)

    def add_peeker(self, receiver):
        """Register a receiver that will have its peek_line method called
        with every line being written to screen.
        """
        self.peeking_receivers.append(receiver)

    def connection_lost(self):
        """The link to the MUD died.

        It is guaranteed that this will be called before close on connection
        event receivers.
        """
        message = time.strftime("Connection closed at %H:%M:%S.")
        colour = HexFGCode(0xFF, 0xAA, 0x00) #lovely orange
        metaline = Metaline(message, RunLengthList([(0, colour)]),
                             RunLengthList([(0, bg_code(BLACK))]))
        self.write(metaline)
        for receiver in self.connection_event_receivers:
            receiver.connection_lost()
        #we might be waiting on the connection to die before we send out
        #close events
        self.telnet = None
        if self._closing_down:
            for receiver in self.connection_event_receivers:
                receiver.close()

    def connection_made(self):
        """The MUD's been connected to."""
        message = time.strftime("Connection opened at %H:%M:%S.")
        colour = HexFGCode(0xFF, 0xAA, 0x00) #lovely orange
        metaline = Metaline(message, RunLengthList([(0, colour)]),
                      RunLengthList([(0, bg_code(BLACK))]))
        self.write(metaline)
        for receiver in self.connection_event_receivers:
            receiver.connection_made()

    def trace_on(self):
        """Turn tracing (verbose printing to the output screen) on."""
        if not self.tracing:
            self.tracing = True
            self.write("TRACE: Tracing enabled!")

    def trace_off(self):
        """Turn tracing off."""
        if self.tracing:
            self.tracing = False
            self.write("TRACE: Tracing disabled!")

    def maybe_do_macro(self, chord):
        """Try and run a macro against the given keychord.

        A return value of True means a macro was found and run, False means
        no macro was found, or a macro returned True (meaning allow the GUI
        to continue handling the keypress).
        """
        if chord in self.macros:
            macro = self.macros[chord]
            allow_gui_continue = False
            try:
                allow_gui_continue = macro(self)
            except Exception:
                traceback.print_exc()
            return not allow_gui_continue
        else:
            return False

    #Going towards the screen

    def receive(self, metaline):
        """Match a line against the triggers and perhaps display it on screen.
        """
        realm = TriggerMatchingRealm(metaline, parent = self,
                                     root = self)
        realm.process()

    def write(self, line, soft_line_start = False):
        """Write a line to the screen.
        
        This forcibly converts its argument to a Metaline.
        """
        if not isinstance(line, (basestring, Metaline)):
            line = str(line)
        if isinstance(line, basestring):
            line = Metaline(line, RunLengthList([(0, fg_code(WHITE, False))]),
                                  RunLengthList([(0, bg_code(BLACK))]),
                            wrap = False, soft_line_start = soft_line_start)
        #we don't need to close off the ends of the note, because thanks to
        #the magic of the ColourCodeParser, each new line is started by the
        #implied colour, so notes can't bleed out into text (though the 
        #reverse can be true).
        self.factory.outputs.write_to_screen(line)
        
        for receiver in self.peeking_receivers:
            receiver.peek_line(line.line)

    #Going towards the MUD.

    def receive_gui_line(self, string):
        """Send lines input into the GUI to the MUD.
        
        NOTE: this may have the power to execute arbitrary Python code. Thus,
        triggers and aliases should avoid using this, as they may be 
        vulnerable to injection from outside sources. Use send instead.
        """
        if string.startswith('/'):
            self.console.push(string[1:])
        else:
            for line in self._escape_parser.parse(string + '\n'):
                self.send(line)

    def send(self, line, echo = True):
        """Match aliases against the line and perhaps send it to the MUD."""
        realm = AliasMatchingRealm(line, echo, parent = self,
                                   root = self)
        realm.process()

    def send_line_to_mud(self, line):
        """Send a line to the MUD."""
        self.telnet.sendLine(line)

