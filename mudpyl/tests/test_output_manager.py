from mudpyl.output_manager import OutputManager
from mudpyl.colours import fg_code, bg_code, BLUE, PURPLE, GREEN, WHITE
from mudpyl.metaline import Metaline, RunLengthList

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
    om = OutputManager(object())
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
                 ('text', 'eggsblah')]
    om.add_output(DummyOutput(expecting))
    colours = [(3, fg_code(BLUE, False)), 
               (6, bg_code(PURPLE)), 
               (6, fg_code(GREEN, True)),
               (9, bg_code(GREEN)), 
               (12, fg_code(WHITE, True)), 
               (16, bg_code(BLUE))]
    text = 'nulfoobarbazspameggsblah'
    om._actually_write_to_screen(colours, text)

def test_actually_write_to_screen_with_overrunning_colours():
    om = OutputManager(object())
    expecting = [('text', 'foo'),
                 ('change', fg_code(GREEN, False)),
                 ('change', bg_code(BLUE))]
    om.add_output(DummyOutput(expecting))
    colours = [(3, fg_code(GREEN, False)),
               (90, bg_code(BLUE))]
    om._actually_write_to_screen(colours, 'foo')

from textwrap import TextWrapper

class DummyOutputManagerWithWrapper(OutputManager):

    def __init__(self):
        self.wrapper = TextWrapper(width = 10, 
                                   drop_whitespace = False)

class TrackingRunLengthList(RunLengthList):

    def __init__(self, *args):
        self.adjustments = []
        RunLengthList.__init__(self, *args)

    def index_adjust(self, index, adjustment):
        RunLengthList.index_adjust(self, index, adjustment)   
        self.adjustments.append((index, adjustment))

class Testwrap_line:

    def setUp(self):
        self.om = DummyOutputManagerWithWrapper()
        self.fores = TrackingRunLengthList([(0, 'fore')])
        self.backs = TrackingRunLengthList([(0, 'back')])
    
    def ml(self, line):
        return Metaline(line, self.fores, self.backs)

    def test_no_alteration_too_short(self):
        line = 'foo'
        res = self.om._wrap_line(self.ml(line))
        assert res.line == line
        assert self.fores.adjustments == self.backs.adjustments == []
    
    def test_no_adjustment_break_on_space_no_adjustment(self):
        line = 'foobarbaz quux'
        res = self.om._wrap_line(self.ml(line))
        assert res.line == 'foobarbaz \nquux'
        assert self.fores.adjustments == self.backs.adjustments == [(10, 1)]

    def test_adjustment_break_in_middle_of_word(self):
        line = 'foobarbazquux'
        res = self.om._wrap_line(self.ml(line))
        assert res.line == 'foobarbazq\nuux'
        assert self.fores.adjustments == self.backs.adjustments == \
               [(10, 1)]

    def test_mixed_break_without_broken_textwrap(self):
        line = 'foo bar baz quuxfoobarbaz foobarbazquux foo'
        res = self.om._wrap_line(self.ml(line))
        assert res.line == \
                     'foo bar \nbaz quuxfo\nobarbaz fo\nobarbazquu\nx foo',\
               res.line
        assert self.fores.adjustments == self.backs.adjustments == \
               [(8, 1), (19, 1), (30, 1), (41, 1)], self.fores.adjustments

class TrackingMetaline(Metaline):

    def __init__(self, *args):
        Metaline.__init__(self, *args)
        self.inserted = []

    def insert(self, ind, string):
        Metaline.insert(self, ind, string)
        self.inserted.append((ind, string))

class PeekingTom:

    def __init__(self):
        self.pought = []

    def peek_line(self, line):
        self.pought.append(line)

class Test_write_to_screen:

    def our_actually_write_to_screen(self, colours, line):
        pass

    def our_wrap_line(self, line):
        assert line is self.ml
        self.second_ml = Metaline("foobar", RunLengthList([(0, 'foo')]), 
                                  RunLengthList([(0, 'foo')]))
        return self.second_ml

    def aws_with_wrap_line_check(self, colours, line):
        assert line is self.second_ml.line

    def aws_with_tes_ting(self, colours, line):
        assert colours == [(0, self.bg), (0, self.fg), (1, 'fg2'), (2, 'bg2'),
                           (3, 'fg3')], colours
        assert line == 'foo'
        self.called = True
    
    def setUp(self):
        self.fg = 'fg'
        self.bg = 'bg'
        self.ml = TrackingMetaline("foo", RunLengthList([(0, self.fg),
                                                         (1, 'fg2'),
                                                         (3, 'fg3')]),
                                   RunLengthList([(0, self.bg),
                                                  (2, 'bg2')]))
        self.om = OutputManager(object())
        self.tom = PeekingTom()
        self.om.add_output(self.tom)
        self.om._actually_write_to_screen = self.our_actually_write_to_screen
        self.called = False

    def test_peeking(self):
        self.om.write_to_screen(self.ml)
        assert self.tom.pought == ["foo"]

    def test_line_insertion_with_hard_line_end_no_sls(self):
        self.om.last_line_end = 'hard'
        self.om.write_to_screen(self.ml)
        assert self.ml.inserted == [(0, '\n')]

    def test_line_insertion_with_hard_line_end_sls(self):
        self.om.last_line_end = 'hard'
        self.ml.soft_line_start = True
        self.om.write_to_screen(self.ml)
        assert self.ml.inserted == [(0, '\n')]

    def test_line_insertion_sle_no_sls(self):
        self.om.last_line_end = 'soft'
        self.om.write_to_screen(self.ml)
        assert self.ml.inserted == [(0, '\n')]

    def test_line_no_insertion_sle_sls(self):
        self.om.last_line_end = 'soft'
        self.ml.soft_line_start = True
        self.om.write_to_screen(self.ml)
        assert self.ml.inserted == [], self.ml.inserted

    def test_respects_Metaline_with_no_line_end(self):
        self.om.last_line_end = None
        self.om.write_to_screen(self.ml)
        assert self.ml.inserted == []

    def test_actually_write_to_screen_call(self):
        self.om._actually_write_to_screen = self.aws_with_tes_ting
        self.om.write_to_screen(self.ml)
        assert self.called

    def test_last_line_end_setting(self):
        self.ml.line_end = object()
        self.om.write_to_screen(self.ml)
        assert self.om.last_line_end is self.ml.line_end

    def test_last_line_end_is_defaultly_None(self):
        assert self.om.last_line_end is None

    def test_with_wrap(self):
        self.om._wrap_line = self.our_wrap_line
        self.om._actually_write_to_screen = self.aws_with_wrap_line_check
        self.ml.wrap = True
        self.om.write_to_screen(self.ml)

class TrackingOutput:

    def __init__(self):
        self.calls = []

    def connection_closed(self):
        self.calls.append('connection_closed')

    def connection_opened(self):
        self.calls.append("connection_opened")

    def close(self):
        self.calls.append("close")

def test_passes_on_connection_closed():
    om = OutputManager(None)
    output = TrackingOutput()
    om.add_output(output)

    om.connection_closed()

    assert output.calls == ['connection_closed']

def test_passes_on_connection_opened():
    om = OutputManager(None)
    output = TrackingOutput()
    om.add_output(output)

    om.connection_opened()

    assert output.calls == ['connection_opened']

class FakeRealm:

    def __init__(self):
        self.closed = False

    def close(self):
        assert not self.closed
        self.closed = True

class FakeFactory:

    def __init__(self):
        self.realm = FakeRealm()

def test_sends_connection_closed_and_close_in_right_order():
    f = FakeFactory()
    om = OutputManager(f)
    output = TrackingOutput()
    om.add_output(output)

    om.closing()
    #simulate Twisted's 'throw-it-over-the-wall' anti-guarantee
    om.connection_closed()

    assert output.calls == ['connection_closed', 'close']

def test_closing_tells_the_realm_to_close():
    f = FakeFactory()
    om = OutputManager(f)

    om.closing()

    assert f.realm.closed
