from mudpyl.gui.gtkcommandline import CommandView

class DummyGUI:

    def __init__(self):
        self.tabdict = DummyTabdict()
        self.realm = None

class DummyTabdict(object):

    def __init__(self):
        self.lines = []

    def add_line(self, line):
        self.lines.append(line)

def test_adding_to_tabdict():
    d = DummyGUI()
    o = CommandView(d)
    line = 'Foo; bar baz qux. Quux! QUUUX!!!'
    o.peek_line(line)
    d.tabdict.lines == [line]


