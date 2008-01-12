"""Contains the widget that displays the text from the MUD."""
from mudpyl.colours import WHITE, BLACK, fg_code, bg_code
import gtk
import time
import pango

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
            self.gui.paused_label.set_text("PAUSED")

    def unpause(self):
        """Restart autoscrolling to new data.
        
        This does not automatically scroll to the buffer's end.
        """
        if self.paused:
            self.paused = False
            self.gui.paused_label.set_text("")
        #scroll to the end of output
        self.scroll_mark_onscreen(self.end_mark)

    def key_pressed_cb(self, widget, event):
        """The user pressed a key while the output window was in focus.

        This forwards it to the command line.
        """
        self.gui.command_line.emit('key-press-event', event)
        return True

    def connection_made(self):
        """The connection's been opened. Inform the user."""
        message = time.strftime("Connection opened at %H:%M:%S.\n")
        tag = self.buffer.create_tag()
        tag.set_property('foreground', '#FFAA00') #lovely orange
        self.buffer.insert_with_tags(self.buffer.get_end_iter(), message, tag)

    def connection_lost(self):
        """The connection's been closed. Inform the user."""
        message = time.strftime("\nConnection closed at %H:%M:%S.")
        tag = self.buffer.create_tag()
        tag.set_property('foreground', '#FFAA00')
        self.buffer.insert_with_tags(self.buffer.get_end_iter(), message, tag)

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

