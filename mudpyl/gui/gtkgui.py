"""A GUI for mudpyl written in PyGTK."""
from mudpyl.gui.gtkoutput import OutputView
from mudpyl.gui.gtkcommandline import CommandView
from mudpyl.gui.tabcomplete import Trie
from twisted.internet.task import LoopingCall
from datetime import datetime, timedelta
import traceback
import gtk

class TimeOnlineLabel(gtk.Label):

    """A display of how long the current session has been online for."""

    def __init__(self):
        gtk.Label.__init__(self)
        self.looping_call = LoopingCall(self.update_time)
        self.start_time = None

    def connection_opened(self):
        """Start ticking."""
        self.start_time = datetime.now()
        #don't leave our display blank
        self.update_time()
        self.looping_call.start(0.5) #update it twice per second

    def connection_closed(self):
        """We only count time online; stop counting."""
        self.looping_call.stop()

    #ignore the rest of the output methods
    def write_out_span(self, arg = None):
        pass
    fg_changed = bg_changed = close = peek_line = write_out_span

    def update_time(self):
        """Should tick once a second. Displays the current running count of
        how long's been spent online.
        """
        delta = datetime.now() - self.start_time
        #chop off microseconds, for neatness
        delta = timedelta(delta.days, delta.seconds)
        self.set_text('Time online: %s' % delta)

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
        self.paused_label = gtk.Label()
        self.time_online = TimeOnlineLabel()
        self._make_widget_body()

    def _make_widget_body(self):
        """Put it all together."""
        self.set_title("%s - mudpyl" % self.realm.factory.name)
        self.connect('destroy', self.destroy_cb)
        self.maximize() #sic

        self.outputs.add_output(self.output_window)
        self.outputs.add_output(self.time_online)

        #never have hscrollbars normally, always have vscrollbars
        self.scrolled_out.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.scrolled_out.add(self.output_window)

        self.scrolled_in.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)
        self.scrolled_in.add(self.command_line)

        #construct the bottom row of indicators and stuff
        labelbox = gtk.HBox()
        #we want the paused indicator to be to the left, because it comes 
        #and goes.
        labelbox.pack_end(self.time_online, expand = False)
        labelbox.pack_end(gtk.VSeparator(), expand = False)
        labelbox.pack_end(self.paused_label, expand = False)

        box = gtk.VBox()

        box.pack_start(self.scrolled_out)
        box.pack_start(gtk.HSeparator(), expand = False)
        box.pack_start(self.scrolled_in, expand = False)
        box.pack_start(labelbox, expand = False)
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
