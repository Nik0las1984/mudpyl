from __future__ import with_statement
from mudpyl.mudconnect import main
from mock import Mock, _importer
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

class OurException(Exception):
    pass

def raiser(exp):
    raise OurException(exp)

class Test_Main:

    def test_blows_up_on_bad_gui(self):
        our_options = Mock(methods = ['gui', 'modulename'])
        our_options.gui = 'foo'
        our_parser = Mock(methods = ['parse_args', 'error'])
        our_parser.error = raiser
        our_parser.parse_args.return_value = our_options
        our_module = Mock()
        our_module.return_value = Mock()
        
        with nested(patched('mudpyl.mudconnect', 'load_file', our_module),
                    patched('mudpyl.mudconnect', 'parser', our_parser)):
            try:
                main()
            except OurException:
                pass
            else:
                assert False

