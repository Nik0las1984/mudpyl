"""Contains the implementation of the command entry widget."""
from mudpyl.gui.commandhistory import CommandHistory
from mudpyl.gui.tabcomplete import Trie
from mudpyl.gui.keychords import from_gtk_event
import gtk
import pango

class CommandView(gtk.Entry):

    """The area where the user enters commands to be sent to the MUD."""

    def __init__(self, gui):
        gtk.Entry.__init__(self)
        self.realm = gui.realm
        self.gui = gui
        self.tabdict = Trie()
        self.hist = CommandHistory(200)
        self.connect('key-press-event', self.key_pressed_cb)
        self.modify_font(pango.FontDescription('monospace 8'))

    buffer = property(gtk.TextView.get_buffer)

    def key_pressed_cb(self, widget, event):
        """The user's pressed a key.

        First, this checks to see if there is a macro bound for the keychord,
        and if there is then it is run; if not, the key is handled by PyGTK.
        """
        chord = from_gtk_event(event)

        if not self.gui.realm.maybe_do_macro(chord):
            #not a macro, so keep processing.
            return False
        return True

    def history_up(self):
        """Move up (ie, back in time) one command in the history."""
        #cursor will be at the end of the line, as it has no left gravity.
        self.set_text(self.hist.advance())
        self.set_position(-1)

    def history_down(self):
        """Move down (ie, forwards in time) one command in the history."""
        self.set_text(self.hist.retreat())
        self.set_position(-1)

    def get_all_text(self):
        """Finger-saving mathod to get all the text from the buffer."""
        bytes = self.get_chars(0, -1)
        return bytes.decode('utf-8')

    def escape_pressed(self):
        """Add the current line to the list of previous commands, and clear
        the buffer.
        """
        self.hist.add_command(self.get_all_text())
        self.set_text('')

    def submit_line(self):
        """Send the current line to the MUD and clear the buffer."""
        text = self.get_all_text()
        self.set_text('')
        self.realm.receive_gui_line(text)
        if not self.realm.server_echo:
            self.hist.add_command(text)

    def tab_complete(self):
        """Tab-completion."""
        line = self.get_all_text()
        #cursor position as an integer from the start of the line
        ind = self.get_position()
        line, ind = self.tabdict.complete(line, ind)
        self.set_text(line)
        #move the cursor to where the tabdict wants it
        self.set_position(ind)

    def add_line_to_tabdict(self, line):
        """Add all the new words in the line to our tabdict."""
        self.tabdict.add_line(line)
