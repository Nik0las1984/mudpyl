"""The GUI part of the client.
"""
from mudpyl.gui.tabcomplete import Trie
from mudpyl.colours import WHITE, BLACK, normal_colours
from mudpyl.gui.keychords import from_wx_event
from mudpyl.gui.commandhistory import CommandHistory
import wax
import wx
import traceback

class OutputWindow(wax.TextBox):
    
    """The MUD's output window. This serves as an Output, as well."""

    def __init__(self, tabdict, command_line, *args, **kwargs):
        self.tabdict = tabdict
        self.command_line = command_line
        wax.TextBox.__init__(self, multiline = True, readonly = True,
                             rich2 = True, size = (800, 500), *args, **kwargs)
        self.Font = ("Courier New", 8)
        self.BackgroundColour = normal_colours[BLACK]
        self.DefaultStyle = wx.TextAttr(normal_colours[WHITE], 
                                        normal_colours[BLACK])
        self.paused = False
        self._pos = None

    def pause(self):
        """Stop the screen moving down with new text."""
        if not self.paused:
            #minor hack to get our top-left character's position
            self._pos = self.GetScrollPos(wx.VERTICAL)
            self.paused = True

    def unpause(self):
        """Allow the screen to keep up with new text again."""
        if self.paused:
            self._pos = None
            self.paused = False

    def OnKeyDown(self, event):
        """The user pressed a key in the output window.
        """
        self.command_line.SetFocus()
        self.command_line.EmulateKeyPress(event)

    def write_out_span(self, text):
        """Write some text to the screen, using the previously set colours.
        """
        self.AppendText(text)
        if self.paused:
            self.SetScrollPos(wx.VERTICAL, self._pos, refresh = True)

    def fg_changed(self, change):
        """Update our writing style."""
        self.DefaultStyle.TextColour = change.triple

    def bg_changed(self, change):
        """Update our background style."""
        self.DefaultStyle.BackgroundColour = change.triple

    def peek_line(self, line):
        '''Add in all our shiny new words to our dictionary.'''
        self.tabdict.add_line(line)

    def close(self):
        """Wax does all our heavy-duty destructing for us."""
        pass

class CommandLine(wax.TextBox):

    """The user's command line."""

    def __init__(self, realm, *args, **kwargs):
        self.realm = realm
        self.output_window = None
        wax.TextBox.__init__(self, process_tab = True, hscroll = True, 
                             size = (800, 40), *args, **kwargs)
        self.hist = CommandHistory(200)
        self.Font = ("Courier New", 8)

    def OnKeyDown(self, event):
        """The user's pressed a key inside the command line.

        Page up & page down are treated specially: these are forwarded to the 
        output screen, since we only have one line.

        Users may also add special semantics to keys via macros.

        """
        if event.KeyCode == wx.WXK_PAGEUP:
            self.output_window.PageUp()
        elif event.KeyCode == wx.WXK_PAGEDOWN:
            self.output_window.PageDown()
        else:
            chord = from_wx_event(event)

            if not self.realm.maybe_do_macro(chord):
                #no macro found
                event.Skip()

    def history_up(self):
        """Go back one command in the history of the command line."""
        self.Value = self.hist.advance()
        self.SetInsertionPointEnd()

    def history_down(self):
        """Go forwards one command in the history of the command line."""
        self.Value = self.hist.retreat()
        self.SetInsertionPointEnd()

    def escape_pressed(self):
        """Enter our current value into the history, then clear ourselves."""
        self.hist.add_command(self.Value)
        self.Value = ''

    def submit_line(self):
        """A line's been entered by the user.

        This grabs its value, clears the command line, adds the line to the
        command history, sends it to the MUD and echoes it to the screen.

        Whew.
        """
        text = self.Value
        self.Value = ''
        self.realm.receive_gui_line(text)
        self.hist.add_command(text)

    def tab_complete(self):
        """Try and find a word seen in the output based on a prefix typed by
        the user.
        """
        line = self.Value
        ind = self.InsertionPoint
        line, ind = self.output_window.tabdict.complete(line, ind)
        self.Value = line
        self.InsertionPoint = ind

class GUIOutput(wax.Frame):

    """The GUI of the MUD client."""

    def __init__(self, outputs, realm, *args, **kwargs):
        #this stuff before the superclass call is what we need to set up prior
        #to self.Body being called, whether with real things or defaults.
        self.output_window = None
        self.command_line = None
        self.outputs = outputs
        self.realm = realm
        realm.factory.gui = self
        self.tabdict = Trie()
        wax.Frame.__init__(self, direction = 'vertical', *args, **kwargs)

    def Body(self):
        """Construct the GUI."""
        #command line
        self.command_line = CommandLine(self.realm, self)

        #output window.
        self.output_window = OutputWindow(self.tabdict, self.command_line, 
                                          self)
        self.command_line.output_window = self.output_window
        self.outputs.add_output(self.output_window)

        self.AddComponent(self.output_window, expand = 'both')
        self.AddComponent(self.command_line, expand = 'horizontal')
        self.command_line.SetFocus()
        self.Pack()

    def OnClose(self, event):
        '''Close everything down.'''
        try:
            self.outputs.closing()
        finally:
            event.Skip()

def configure(factory):
    """Install the right reactor and start a GUI up."""
    from twisted.internet import wxreactor
    wxreactor.install()
    app = wax.Application(GUIOutput, factory.outputs, factory.realm)
    from twisted.internet import reactor
    #pylint kicks up a major fuss about these lines, but that's because 
    #Twisted does some hackery with the reactor namespace.
    #pylint: disable-msg=E1101
    reactor.registerWxApp(app)
