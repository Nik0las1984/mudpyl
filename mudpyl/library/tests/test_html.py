from __future__ import with_statement
from StringIO import StringIO
from mudpyl.library import html
from mudpyl.library.html import HTMLLogOutput
from cgi import escape
from mudpyl.colours import HexFGCode, HexBGCode, bg_code, fg_code, WHITE, RED,\
     PURPLE, GREEN
from mock import _importer, Mock, sentinel
from mudpyl.metaline import Metaline, RunLengthList, simpleml

class Logger(HTMLLogOutput):

    log_postamble = "POSTAMBLE"
    colour_change = "COLOUR CHANGE %s %s"
    connection_lost_message = 'closing time format goes here'
    connection_made_message = 'opening time format goes here'

    def __init__(self, log):
        self.log = log
        self.fore = Mock()
        self.back = Mock()
        self.method_calls = []

    def write_out_span(self, span):
        self.method_calls.append(("write_out_span", (span,), {}))
        HTMLLogOutput.write_out_span(self, span)

    def change_colour(self):
        self.method_calls.append(("change_colour", (), {}))
        HTMLLogOutput.change_colour(self)

class Test_HTMLLogOutput:

    def setUp(self):
        self.f = StringIO()
        self.o = Logger(self.f)
        self.o.fore.as_hex = self.o.fore.ground = 'fore'
        self.o.back.as_hex = self.o.back.ground = 'back'
        self.f1 = fg_code(WHITE, False)
        self.f2 = fg_code(GREEN, True)
        self.b1 = bg_code(RED)
        self.b2 = bg_code(PURPLE)

    def test_write_out_span_writes_it_out(self):
        self.o.write_out_span("foo")
        assert self.f.getvalue() == 'foo'

    def test_write_out_span_escapes_text(self):
        self.o.write_out_span("<foo>")
        assert self.f.getvalue() == escape('<foo>')

    def test_change_colour_writes_out_new_colour(self):
        self.o.back.as_hex = 'newback'
        self.o.change_colour()
        assert self.f.getvalue() == 'COLOUR CHANGE fore newback', \
               self.f.getvalue()

    def test_metalineReceived_calls_write_out_span(self):
        self.o.write_out_span = Mock()
        self.o.metalineReceived(simpleml("foo", self.o.fore, self.o.back))
        assert self.o.write_out_span.call_args_list == [(("foo",), {})]

    def test_metalineReceived_changes_colour_if_needed(self):
        self.o.metalineReceived(simpleml("foo", self.f1, self.b1))
        print self.o.method_calls
        assert self.o.method_calls == [("change_colour", (), {}),
                                       ("write_out_span", ("foo",), {})]

    def test_metalineReceived_doesnt_change_colour_if_not_needed(self):
        self.o.change_colour = Mock()
        self.o.metalineReceived(simpleml("foo", self.o.fore, self.o.back))
        assert not self.o.change_colour.called

    def test_metalineReceived_change_colour_mid_span_calls_change_colour(self):
        self.o.metalineReceived(Metaline("foobarbaz",
                                         RunLengthList([(0, self.f1),
                                                        (3, self.f2)]),
                                         RunLengthList([(0, self.b1),
                                                        (6, self.b2)])))
        assert self.o.method_calls == [("change_colour", (), {}),
                                       ("write_out_span", ("foo",), {}),
                                       ("change_colour", (), {}),
                                       ("write_out_span", ("bar",), {}),
                                       ("change_colour", (), {}),
                                       ("write_out_span", ("baz",), {})]

    def test_metalineReceived_sets_fore_and_back_mid_span(self):
        colours = []
        self.o.change_colour = lambda: colours.append((self.o.fore,
                                                       self.o.back))
        self.o.metalineReceived(Metaline("foobarbaz",
                                         RunLengthList([(0, self.f1),
                                                        (3, self.f2)]),
                                         RunLengthList([(0, self.b1),
                                                        (6, self.b2)])))
        assert colours == [(self.f1, self.b1),
                           (self.f2, self.b1),
                           (self.f2, self.b2)]

    def test_metalineReceived_calls_change_colour_for_overrun_colours(self):
        self.o.metalineReceived(Metaline("foo",
                                         RunLengthList([(0, self.f1),
                                                        (3, self.f2)]),
                                         RunLengthList([(0, self.b1),
                                                        (6, self.b2)])))
        print self.o.method_calls
        assert self.o.method_calls == [("change_colour", (), {}),
                                       ("write_out_span", ("foo",), {}),
                                       ("change_colour", (), {})]

    def test_metalineReceived_sets_fore_and_back_for_overruns(self):
        colours = []
        self.o.change_colour = lambda: colours.append((self.o.fore,
                                                       self.o.back))
        self.o.metalineReceived(Metaline("foo",
                                         RunLengthList([(0, self.f1),
                                                        (3, self.f2)]),
                                         RunLengthList([(0, self.b1),
                                                        (6, self.b2)])))
        assert colours == [(self.f1, self.b1),
                           (self.f2, self.b2)]

class MockFile:

    def __init__(self):
        self.written = ''
        self.closed = False

    def write(self, data):
        self.written += data

    def close(self):
        self.closed = True

class Test_close:

    def setUp(self):
        self.f = MockFile()
        self.o = Logger(self.f)

    def test_close_writes_postamble(self):
        self.o.close()
        assert self.f.written == 'POSTAMBLE'

    def test_close_closes_file(self):
        self.o.close()
        assert self.f.closed

from mudpyl.net.telnet import TelnetClientFactory
from contextlib import contextmanager, nested

@contextmanager
def patched(target, attribute, new = None):
    if isinstance(target, basestring):
        target = _importer(target)

    if new is None:
        new = Mock()

    original = getattr(target, attribute)
    setattr(target, attribute, new)

    try:
        yield new
    finally:
        setattr(target, attribute, original)

class TestHTMLLogOutputInitialisation:

    def setUp(self):
        self.time = Mock(methods = ['strftime'])
        self.time.strftime.return_value = "FOO %(name)s"
        self.factory = TelnetClientFactory('baz', None, None)
        self.realm = self.factory.realm
        self.open = Mock()
        self.open.return_value = MockFile()

    def test_opens_file_in_append_mode(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            log = HTMLLogOutput(self.realm, None)
        assert self.open.call_args == (("FOO baz", "a"), {})

    def test_passes_given_format_to_strftime(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            log = HTMLLogOutput(self.realm, "BAR")
        assert self.time.method_calls == [('strftime', ('BAR',), {})]

    def test_sets_opened_file_to_self_log(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            print 'opening'
            log = HTMLLogOutput(self.realm, "BAR")
            print 'should be opened'
        print log.log, self.open.return_value
        assert log.log is self.open.return_value

    def test_writes_preamble_to_file(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            log = HTMLLogOutput(self.realm, "BAR")
        assert self.open.return_value.written == HTMLLogOutput.log_preamble

from mudpyl.library.html import HTMLLoggingModule

def test_HTMLLoggingModule_is_main_initialises_html_log():
    f = TelnetClientFactory(None, 'ascii', None)
    m = Mock()
    with nested(patched("mudpyl.library.html", "HTMLLogOutput", m),
                patched("mudpyl.library.html", "time")):
        mod = HTMLLoggingModule(f.realm)
        mod.logplace = sentinel.logplace
        mod.is_main(f.realm)
    assert m.call_args_list == [((f.realm, sentinel.logplace), {})]

