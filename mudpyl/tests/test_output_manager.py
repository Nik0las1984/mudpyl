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
        self.om._actually_write_to_screen = self.our_actually_write_to_screen
        self.called = False

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

from mock import sentinel, Mock

class Test_peek_metaline:

    def setUp(self):
        self.om = OutputManager(None)

    def test_addition(self):
        self.om.add_metaline_peeker(sentinel.peeker)
        assert sentinel.peeker in self.om.metaline_peekers

    def test_calls_for_each_written_line(self):
        ml = Metaline('', RunLengthList([(0, fg_code(WHITE, False))]),
                      RunLengthList([(0, bg_code(PURPLE))]))
        m = Mock()
        self.om.add_metaline_peeker(m)
        self.om.write_to_screen(ml)
        assert m.peek_metaline.called
        assert m.peek_metaline.call_args[0] == (ml,)
