from __future__ import with_statement
from mudpyl.mudconnect import main
from mudpyl.modules import BaseModule
from mock import Mock, _importer, patch, sentinel
from contextlib import contextmanager, nested

@contextmanager
def patched(target, attribute, new = None):
    if isinstance(target, basestring):
        target = _importer(target)

    if new is None:
        new = Mock()

    if hasattr(target, attribute):
        original = getattr(target, attribute)
    setattr(target, attribute, new)

    try:
        yield new
    finally:
        try:
            setattr(target, attribute, original)
        except NameError:
            pass

class OurMainModule(BaseModule):
    name = sentinel.name
    host = sentinel.host
    port = sentinel.port

class Test_Main:

    @patch('sys', 'argv', ['foo', '-g', 'flarg'])
    @patch('sys', 'stderr')
    def test_blows_up_on_bad_gui(self, our_stderr):
        our_module = Mock()
        our_module.return_value = Mock()
        
        with patched('mudpyl.mudconnect', 'load_file', our_module):
            try:
                main()
            except SystemExit:
                err_string = our_stderr.write.call_args[0][0]
                print err_string
                assert "invalid choice: 'flarg'" in err_string
            else:
                assert False

    @patch("mudpyl.mudconnect", "parser")
    @patch("mudpyl.mudconnect", "load_file")
    @patch("mudpyl.gui.gtkgui", "configure", Mock())
    def test_loads_file_specified_on_command_line(self, mock_parser,
                                                  mock_load_file):
        mock_parser.parse_args.return_value = mock_options = Mock()
        mock_options.modulename = sentinel.modulename
        mock_options.gui = "gtk"
        mock_load_file.return_value = OurMainModule
        with patched("twisted.internet", "reactor"):
            main()
        assert mock_load_file.call_args_list == [((sentinel.modulename,),
                                                  {})]
