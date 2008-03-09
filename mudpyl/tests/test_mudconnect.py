from __future__ import with_statement
from mudpyl.mudconnect import main
from mock import Mock, _importer, patch
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

