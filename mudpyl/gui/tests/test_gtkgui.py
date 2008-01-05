from mudpyl.gui.gtkgui import OutputView

class DummyGUI:

    def __init__(self):
        self.tabdict = DummyTabdict()

class DummyTabdict(object):

    def __init__(self):
        self.lines = []

    def add_line(self, line):
        self.lines.append(line)

def test_adding_to_tabdict():
    d = DummyGUI()
    o = OutputView(d)
    line = 'Foo; bar baz qux. Quux! QUUUX!!!'
    o.peek_line(line)
    d.tabdict.lines == [line]

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
