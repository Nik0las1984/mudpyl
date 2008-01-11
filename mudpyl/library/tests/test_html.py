from StringIO import StringIO
from mudpyl.library import html
from mudpyl.library.html import HTMLLogOutput
from cgi import escape
from mudpyl.colours import HexFGCode, HexBGCode
import time

class Logger(HTMLLogOutput):

    log_postamble = "POSTAMBLE"
    colour_change = "COLOUR CHANGE %s %s"
    connection_closed_message = 'closing time format goes here'
    connection_opened_message = 'opening time format goes here'

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

    def test_connection_opened_writes_out_time_of_opening(self):
        t = FakeTimeModule()
        html.time = t
        self.o.connection_opened()
        assert self.f.getvalue() == 'FOO %(name)s'
        assert t.formats == ['opening time format goes here']
        html.time = time


    def test_connection_closed_writes_out_time_of_closing(self):
        t = FakeTimeModule()
        html.time = t
        self.o.connection_closed()
        assert self.f.getvalue() == 'FOO %(name)s'
        assert t.formats == ['closing time format goes here']
        html.time = time

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

class FakeTimeModule:

    def __init__(self):
        self.formats = []

    def strftime(self, format):
        self.formats.append(format)
        return 'FOO %(name)s'

class TestHTMLLogOutputInitialisation:

    def setUp(self):
        html.open = self.our_open
        html.time = self.time = FakeTimeModule()
        self.factory = TelnetClientFactory('baz')
        self.outputs = self.factory.outputs
        self.opened = []
        self.open_returns = MockFile()

    def tearDown(self):
        html.open = open
        html.time = time

    def our_open(self, name, mode):
        assert mode == 'a'
        self.opened.append(name)
        return self.open_returns

    def test_adds_itself_to_output_manager(self):
        log = HTMLLogOutput(self.outputs, None)
        assert self.outputs.outputs == [log]

    def test_passes_given_format_to_strftime(self):
        HTMLLogOutput(self.outputs, 'BAR')
        assert self.time.formats == ['BAR']

    def test_uses_return_value_of_strftime_as_filename(self):
        HTMLLogOutput(self.outputs, None)
        assert self.opened == ['FOO baz']

    def test_sets_opened_file_to_self_log(self):
        log = HTMLLogOutput(self.outputs, None)
        assert log.log is self.open_returns

    def test_writes_preamble_to_file(self):
        HTMLLogOutput(self.outputs, None)
        assert self.open_returns.written == HTMLLogOutput.log_preamble

from mudpyl.library.html import HTMLLoggingModule

def test_HTMLLoggingModule_is_main_initialises_html_log():
    def fake_module(outputs, logplace_received):
        assert outputs is f.outputs
        assert logplace is logplace_received
        calls.append(True)
    calls = []
    html.HTMLLogOutput = fake_module

    f = TelnetClientFactory(None)
    logplace = object()

    m = HTMLLoggingModule(f.realm)
    m.logplace = logplace
    m.is_main()
    assert calls == [True]

    html.HTMLLogOutput = HTMLLogOutput
