from mudpyl.net.telnet import TelnetClientFactory
from mudpyl.gui.bindings import tab_pressed, up_pressed, escape_pressed, \
                                enter_pressed, pause_toggle, down_pressed
from mudpyl.gui.gtkcommandline import CommandView
from mudpyl.gui.gtkgui import GUI
from mudpyl.gui.gtkoutput import OutputView
from mock import Mock

class Test_bindings:

    def setUp(self):
        self.factory = TelnetClientFactory(None, 'ascii', None)
        self.factory.gui = Mock(spec = GUI,
                                #instance variables
                                methods = ['output_window', 'command_line'])
        self.factory.output_window = Mock(spec = CommandView)
        self.factory.command_line = Mock(spec = OutputView)

    def test_enter_pressed_submits_line(self):
        enter_pressed(self.factory.realm)
        assert self.factory.gui.command_line.submit_line.called

    def test_escape_pressed(self):
        escape_pressed(self.factory.realm)
        assert self.factory.gui.command_line.escape_pressed.called

    def test_tab_pressed_tab_completes(self):
        tab_pressed(self.factory.realm)
        assert self.factory.gui.command_line.tab_complete.called 

    def test_up_pressed_navigates_up_the_history(self):
        up_pressed(self.factory.realm)
        assert self.factory.gui.command_line.history_up.called 

    def test_down_pressed_navigates_down_the_history(self):
        down_pressed(self.factory.realm)
        assert self.factory.gui.command_line.history_down.called 

    def test_pause_toggle_unpauses_when_paused(self):
        self.factory.gui.output_window.paused = True
        pause_toggle(self.factory.realm)
        assert self.factory.gui.output_window.unpause.called 

    def test_pause_toggle_pauses_when_not_paused(self):
        self.factory.gui.output_window.paused = False
        pause_toggle(self.factory.realm)
        assert self.factory.gui.output_window.pause.called 

#XXX: test the key setting in gui_macros
