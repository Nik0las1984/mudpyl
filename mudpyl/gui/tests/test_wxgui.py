from mudpyl.gui.wxgui import OutputWindow

class Dummy(OutputWindow):

    def __init__(self):
        pass

class DummyTabdict(object):

    def __init__(self):
        self.lines = []

    def add_line(self, line):
        self.lines.append(line)

def test_adding_to_tabdict():
    d = Dummy()
    d.tabdict = DummyTabdict()
    line = 'Foo; bar baz qux. Quux! QUUUX!!!'
    d.peek_line(line)
    d.tabdict.lines == [line]


