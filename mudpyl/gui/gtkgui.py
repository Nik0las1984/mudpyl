"""A GUI for mudpyl written in PyGTK."""
from mudpyl.gui.keychords import from_gtk_event
from mudpyl.gui.commandhistory import CommandHistory
from mudpyl.gui.tabcomplete import Trie
from mudpyl.colours import WHITE, BLACK, fg_code, bg_code
import traceback
import gtk
import pango

class CommandView(gtk.TextView):

    """The area where the user enters commands to be sent to the MUD."""

    def __init__(self, gui):
        gtk.TextView.__init__(self)
        self.realm = gui.realm
        self.gui = gui
        self.hist = CommandHistory(200)
        self.connect('key-press-event', self.key_pressed_cb)
        self.modify_font(pango.FontDescription('monospace 8'))

    buffer = property(gtk.TextView.get_buffer)

    def key_pressed_cb(self, widget, event):
        """The user's pressed a key.

        This checks to see if it's a page up or page down key, because these
        are forwarded to the output window, and then looks to see if there is
        a macro defined for this key.

        If not, it is added to the buffer of text.
        """
        chord = from_gtk_event(event)

        if chord.key == 'page up':
            self.gui.scrolled_out.emit('scroll-child', 
                                       gtk.SCROLL_PAGE_BACKWARD,
                                       False)
        elif chord.key == 'page down':
            self.gui.scrolled_out.emit('scroll-child',
                                       gtk.SCROLL_PAGE_FORWARD,
                                       False)
        elif self.gui.realm.maybe_do_macro(chord):
            pass
        else:
            #not a macro, so keep processing
            return False
        return True

    def history_up(self):
        """Move up (ie, back in time) one command in the history."""
        #cursor will be at the end of the line, as it has no left gravity.
        self.buffer.set_text(self.hist.advance())

    def history_down(self):
        """Move down (ie, forwards in time) one command in the history."""
        self.buffer.set_text(self.hist.retreat())

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
        line, ind = self.gui.tabdict.complete(line, ind)
        self.buffer.set_text(line)
        #move the cursor to where the tabdict wants it
        newiter = self.buffer.get_iter_at_offset(ind)
        self.buffer.place_cursor(newiter)

class OutputView(gtk.TextView):

    """The display for all the text received from the MUD."""

    def __init__(self, gui):
        gtk.TextView.__init__(self)
        #the identity of the return value of get_buffer() doesn't seem to be
        #stable. before, we used a property, but now we just get it once and
        #leave it at that because GTK complains about the non-identicality
        #of them.
        self.gui = gui
        self.buffer = self.get_buffer()
        self.paused = False
        self.fg_tag = None
        self.bg_tag = None
        self.fg_changed(fg_code(WHITE, False))
        self.bg_changed(bg_code(BLACK))
        self.end_mark = self.buffer.create_mark('end_mark', 
                                                self.buffer.get_end_iter(), 
                                                False)
        self.connect('key-press-event', self.key_pressed_cb)

        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_CHAR)
        self.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0)) #sic
        self.modify_font(pango.FontDescription('monospace 8'))

    def pause(self):
        """Stop autoscrolling to new data."""
        if not self.paused:
            self.paused = True

    def unpause(self):
        """Restart autoscrolling to new data.
        
        This does not automatically scroll to the buffer's end.
        """
        if self.paused:
            self.paused = False
        #scroll to the end of output
        self.scroll_mark_onscreen(self.end_mark)

    def key_pressed_cb(self, widget, event):
        """The user pressed a key while the output window was in focus.

        This forwards it to the command line.
        """
        self.gui.command_line.emit('key-press-event', event)
        return True

    def peek_line(self, line):
        '''Add in all our shiny new words to our dictionary.'''
        self.gui.tabdict.add_line(line)

    def write_out_span(self, text):
        """Write a span of text to the window using the current colours.

        This will autoscroll to the end if we are not paused.
        """
        bytes = text.encode('utf-8')
        self.buffer.insert_with_tags(self.buffer.get_end_iter(), bytes, 
                                     self.fg_tag, self.bg_tag)
        if not self.paused:
            self.scroll_mark_onscreen(self.end_mark)

    def fg_changed(self, change):
        """Change the foreground colour of the text that will be written."""
        self.fg_tag = self.buffer.create_tag()
        self.fg_tag.set_property('foreground', '#' + change.tohex())
        self.fg_tag.set_property('foreground-set', True)

    def bg_changed(self, change):
        """Change the background colour of the text that will be written."""
        self.bg_tag = self.buffer.create_tag()
        self.bg_tag.set_property('background', '#' + change.tohex())
        self.bg_tag.set_property('background-set', True)

    def close(self):
        """We don't much care about these. GTK cleans up afterwards, and we
        don't want to poof right away when the connection closes.
        """
        pass

class GUI(gtk.Window):

    """The toplevel window. Contains the command line and the output view."""

    def __init__(self, outputs, realm):
        gtk.Window.__init__(self)
        self.outputs = outputs
        self.realm = realm
        realm.factory.gui = self
        self.tabdict = Trie()
        self.command_line = CommandView(self)
        self.output_window = OutputView(self)
        self.scrolled_out = gtk.ScrolledWindow()
        self.scrolled_in = gtk.ScrolledWindow()
        self._make_widget_body()

    def _make_widget_body(self):
        """Put it all together."""
        self.set_title("%s - mudpyl" % self.realm.factory.name)
        self.connect('destroy', self.destroy_cb)
        self.maximize() #sic

        self.outputs.add_output(self.output_window)
        self.command_line.output_window = self.output_window

        #never have hscrollbars normally, always have vscrollbars
        self.scrolled_out.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.scrolled_out.add(self.output_window)

        self.scrolled_in.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)
        self.scrolled_in.add(self.command_line)

        box = gtk.VBox()

        box.pack_start(self.scrolled_out)
        box.pack_start(gtk.HSeparator(), expand = False)
        box.pack_start(self.scrolled_in, expand = False)
        self.add(box)

        self.show_all()

    def destroy_cb(self, widget, data = None):
        """Close everything down."""
        try:
            self.outputs.closing()
        except Exception:
            #swallow-log traceback here, because exiting gracefully is fairly
            #important. The traceback is written to stdout (or is it stderr?
            #one of the two, anyway), so we just plug on into the finally
            #clause.
            traceback.print_exc()
        finally:
            #if the reactor's been started, this will run straight away, else
            #it'll make the reactor die as soon as we do start. oh, and, we
            #can't import out there, because we may not have installed the
            #right reactor yet.
            from twisted.internet import reactor
            #and, of course, because of Twisted's namespace hackery, pylint
            #gets confused.
            #pylint: disable-msg= E1101
            reactor.callWhenRunning(reactor.stop)
            #pylint: enable-msg= E1101
            return True

def configure(factory):
    """Set the right reactor up and get the GUI going."""
    from twisted.internet import gtk2reactor
    gtk2reactor.install()
    GUI(factory.outputs, factory.realm)
