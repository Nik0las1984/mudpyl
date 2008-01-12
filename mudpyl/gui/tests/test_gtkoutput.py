from mudpyl.gui.gtkoutput import OutputView

class DummyLabel:

    def set_text(self, text):
        pass

class DummyGUI:

    def __init__(self):
        self.paused_label = DummyLabel()

class TestPausing:

    def setUp(self):
        self.output_view = OutputView(DummyGUI())

    def test_paused_is_defaultly_false(self):
        assert not self.output_view.paused

    def test_pause_pauses_if_unpaused(self):
        self.output_view.pause()
        assert self.output_view.paused

    def test_pause_stays_paused_if_paused(self):
        self.output_view.paused = True
        self.output_view.pause()
        assert self.output_view.paused

    def test_unpause_stays_unpaused_if_unpaused(self):
        self.output_view.unpause()
        assert not self.output_view.paused

    def test_unpause_unpauses_if_paused(self):
        self.output_view.paused = True
        self.output_view.unpause()
        assert not self.output_view.paused
