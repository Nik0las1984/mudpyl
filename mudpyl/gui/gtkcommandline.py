"""Contains the implementation of the command entry widget."""
from mudpyl.gui.commandhistory import CommandHistory
from mudpyl.gui.tabcomplete import Trie
from mudpyl.gui.keychords import from_gtk_event
import gtk
import pango

class CommandView(gtk.TextView):

    """The area where the user enters commands to be sent to the MUD."""

    def __init__(self, gui):
        gtk.TextView.__init__(self)
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
        self.buffer.set_text(self.hist.advance())
        self.scroll_mark_onscreen(self.buffer.get_insert())

    def history_down(self):
        """Move down (ie, forwards in time) one command in the history."""
        self.buffer.set_text(self.hist.retreat())
        self.scroll_mark_onscreen(self.buffer.get_insert())

    def get_all_text(self):
        """Finger-saving mathod to get all the text from the buffer."""
        bytes = self.buffer.get_text(self.buffer.get_start_iter(), 
                                     self.buffer.get_end_iter())
        return bytes.decode('utf-8')

    def escape_pressed(self):
        """Add the current line to the list of previous commands, and clear
        the buffer.
        """
        self.hist.add_command(self.get_all_text())
        self.buffer.set_text('')

    def submit_line(self):
        """Send the current line to the MUD and clear the buffer."""
        text = self.get_all_text()
        self.buffer.set_text('')
        self.realm.receive_gui_line(text)
        self.hist.add_command(text)

    def tab_complete(self):
        """Tab-completion."""
        line = self.get_all_text()
        cursoriter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        #cursor position as an integer from the start of the line
        ind = cursoriter.get_offset()
        line, ind = self.tabdict.complete(line, ind)
        self.buffer.set_text(line)
        #move the cursor to where the tabdict wants it
        newiter = self.buffer.get_iter_at_offset(ind)
        self.buffer.place_cursor(newiter)

    def peek_line(self, line):
        """Add all the new words in the line to our tabdict."""
        self.tabdict.add_line(line)
