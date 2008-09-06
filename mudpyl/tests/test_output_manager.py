from mudpyl.output_manager import OutputManager
from mudpyl.colours import fg_code, bg_code, BLUE, PURPLE, GREEN, WHITE
from mudpyl.metaline import Metaline, RunLengthList, simpleml

class DummyOutput:

    def __init__(self, expecting):
        self.expecting = expecting

    def write_out_span(self, span):
        expected = self.expecting.pop(0)
        assert expected == ('text', span)

    def fg_changed(self, change):
        expected = self.expecting.pop(0)
        assert expected == ('change', change)
    bg_changed = fg_changed

#XXX: non-public-ish interface
def test_actually_write_to_screen():
    om = OutputManager(Mock())
    expecting = [('text', 'nul'),
                 ('change', fg_code(BLUE, False)),
                 ('text', 'foo'),
                 ('change', bg_code(PURPLE)),
                 ('change', fg_code(GREEN, True)),
                 ('text', 'bar'),
                 ('change', bg_code(GREEN)),
                 ('text', 'baz'),
                 ('change', fg_code(WHITE, True)),
                 ('text', 'spam'),
                 ('change', bg_code(BLUE)),
                 ('text', 'eggsblah'),
                 ('change', fg_code(GREEN, False)),
                 ('change', bg_code(PURPLE))]
    om.add_output(DummyOutput(expecting))
    colours = [(3, fg_code(BLUE, False)), 
               (6, bg_code(PURPLE)), 
               (6, fg_code(GREEN, True)),
               (9, bg_code(GREEN)), 
               (12, fg_code(WHITE, True)), 
               (16, bg_code(BLUE)),
               (500, fg_code(GREEN, False)),
               (501, bg_code(PURPLE))]
    text = 'nulfoobarbazspameggsblah'
    om._actually_write_to_screen(colours, text)

def test_actually_write_to_screen_with_overrunning_colours():
    om = OutputManager(Mock())
    expecting = [('text', 'foo'),
                 ('change', fg_code(GREEN, False)),
                 ('change', bg_code(BLUE))]
    om.add_output(DummyOutput(expecting))
    colours = [(3, fg_code(GREEN, False)),
               (90, bg_code(BLUE))]
    om._actually_write_to_screen(colours, 'foo')

from mock import sentinel, Mock

def test_metalineReceived_passes_set_of_colours_and_line_to_aws():
    om = OutputManager(Mock())
    om._actually_write_to_screen = Mock()

    om.metalineReceived(Metaline("foobar", RunLengthList([(0, sentinel.f1),
                                                          (3, sentinel.f2)]),
                                 RunLengthList([(0, sentinel.b1),
                                                (3, sentinel.b2)])))

    colours, line = om._actually_write_to_screen.call_args[0]
    assert set(colours) == set([(0, sentinel.f1), (3, sentinel.f2),
                                (0, sentinel.b1), (3, sentinel.b2)])
    assert line == 'foobar'

def test_forwards_connectionMade():
    om = OutputManager(Mock())
    o = Mock()
    om.add_output(o)
    om.connectionMade()
    calls = [name for (name, a, kw) in o.method_calls]
    assert calls == ["connectionMade"]

def test_forwards_connectionLost():
    om = OutputManager(Mock())
    o = Mock()
    om.add_output(o)
    om.connectionLost()
    calls = [name for (name, a, kw) in o.method_calls]
    assert calls == ['connectionLost']

def test_forwards_close():
    om = OutputManager(Mock())
    o = Mock()
    om.add_output(o)
    om.close()
    calls = [name for (name, a, kw) in o.method_calls]
    assert calls == ['close']

def test_adds_itself_to_realm():
    f = Mock()
    om = OutputManager(f)
    assert f.realm.addProtocol.call_args[0][0] is om
