from __future__ import with_statement
from StringIO import StringIO
from mudpyl.library import html
from mudpyl.library.html import HTMLLogOutput
from cgi import escape
from mudpyl.colours import HexFGCode, HexBGCode
from mock import _importer, Mock, sentinel

class Logger(HTMLLogOutput):

    log_postamble = "POSTAMBLE"
    colour_change = "COLOUR CHANGE %s %s"
    connection_lost_message = 'closing time format goes here'
    connection_made_message = 'opening time format goes here'

    def __init__(self, log):
        self.log = log

    class outputs:

        fore = HexFGCode(0xF0, 0x0B, 0xA8)
        back = HexBGCode(0xA2, 0xE6, 0x65)

class Test_HTMLLogOutput:

    def setUp(self):
        self.f = StringIO()
        self.o = Logger(self.f)

    def test_write_out_span_writes_it_out(self):
        self.o.write_out_span("foo")
        assert self.f.getvalue() == 'foo'

    def test_write_out_span_escapes_text(self):
        self.o.write_out_span("<foo>")
        assert self.f.getvalue() == escape('<foo>')

    def test_fg_changed_writes_out_new_colour(self):
        self.o.fg_changed(None)
        assert self.f.getvalue() == 'COLOUR CHANGE f00ba8 a2e665', \
               self.f.getvalue()

    def test_bg_changed_writes_out_new_colour(self):
        self.o.bg_changed(None)
        assert self.f.getvalue() == 'COLOUR CHANGE f00ba8 a2e665'

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
        self.outputs = self.factory.outputs
        self.realm = self.factory.realm
        self.open = Mock()
        self.open.return_value = MockFile()

    def test_adds_itself_to_output_manager(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            log = HTMLLogOutput(self.outputs, self.realm, None)
        assert self.outputs.outputs == [log]

    def test_opens_file_in_append_mode(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            log = HTMLLogOutput(self.outputs, self.realm, None)
        assert self.open.call_args == (("FOO baz", "a"), {})

    def test_passes_given_format_to_strftime(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            log = HTMLLogOutput(self.outputs, self.realm, "BAR")
        assert self.time.method_calls == [('strftime', ('BAR',), {})]

    def test_sets_opened_file_to_self_log(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            print 'opening'
            log = HTMLLogOutput(self.outputs, self.realm, "BAR")
            print 'should be opened'
        print log.log, self.open.return_value
        assert log.log is self.open.return_value

    def test_writes_preamble_to_file(self):
        with nested(patched('__builtin__', 'open', self.open),
                    patched('mudpyl.library.html', 'time', self.time)):
            log = HTMLLogOutput(self.outputs, self.realm, "BAR")
        assert self.open.return_value.written == HTMLLogOutput.log_preamble

from mudpyl.library.html import HTMLLoggingModule

def test_HTMLLoggingModule_is_main_initialises_html_log():
    f = TelnetClientFactory(None, 'ascii', None)
    m = Mock()
    with nested(patched("mudpyl.library.html", "HTMLLogOutput", m),
                patched("mudpyl.library.html", "time")):
        mod = HTMLLoggingModule(f.realm)
        mod.logplace = sentinel.logplace
        mod.is_main()
    assert m.call_args_list == [((f.outputs, f.realm, sentinel.logplace), {})]

