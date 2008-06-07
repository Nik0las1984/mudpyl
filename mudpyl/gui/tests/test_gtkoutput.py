from mudpyl.gui.gtkoutput import OutputView
from mock import Mock

class TestPausing:

    def setUp(self):
        self.output_view = OutputView(Mock())

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
