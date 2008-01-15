from mudpyl.net.telnet import TelnetClientFactory
from mudpyl.gui.bindings import tab_pressed, up_pressed, escape_pressed, \
                                enter_pressed, pause_toggle, down_pressed

class MockCommandLine:

    def __init__(self):
        self.called = []

    def submit_line(self):
        self.called.append('submit_line')

    def escape_pressed(self):
        self.called.append("escape_pressed")

    def tab_complete(self):
        self.called.append("tab_complete")

    def history_up(self):
        self.called.append("history_up")

    def history_down(self):
        self.called.append("history_down")

class MockOutputWindow:

    def __init__(self):
        self.called = []
        self.paused = False

    def pause(self):
        self.called.append('pause')

    def unpause(self):
        self.called.append("unpause")

class FakeGUI:

    def __init__(self):
        self.output_window = MockOutputWindow()
        self.command_line = MockCommandLine()

class Test_bindings:

    def setUp(self):
        self.factory = TelnetClientFactory(None, 'ascii')
        self.factory.gui = FakeGUI()

    def test_enter_pressed_submits_line(self):
        enter_pressed(self.factory.realm)
        assert self.factory.gui.command_line.called == ['submit_line']

    def test_escape_pressed(self):
        escape_pressed(self.factory.realm)
        assert self.factory.gui.command_line.called == ['escape_pressed']

    def test_tab_pressed_tab_completes(self):
        tab_pressed(self.factory.realm)
        assert self.factory.gui.command_line.called == ['tab_complete']

    def test_up_pressed_navigates_up_the_history(self):
        up_pressed(self.factory.realm)
        assert self.factory.gui.command_line.called == ['history_up']

    def test_down_pressed_navigates_down_the_history(self):
        down_pressed(self.factory.realm)
        assert self.factory.gui.command_line.called == ['history_down']

    def test_pause_toggle_unpauses_when_paused(self):
        self.factory.gui.output_window.paused = True
        pause_toggle(self.factory.realm)
        assert self.factory.gui.output_window.called == ['unpause']

    def test_pause_toggle_pauses_when_not_paused(self):
        self.factory.gui.output_window.paused = False
        pause_toggle(self.factory.realm)
        assert self.factory.gui.output_window.called == ['pause']

#XXX: test the key setting in gui_macros
