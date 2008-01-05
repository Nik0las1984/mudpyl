from mudpyl.escape_parser import EscapeParser, InvalidInput, InvalidEscape

class TestEscapes(object):
 
    def setUp(self):
        self.eparser = EscapeParser()

    tests = [('foo\n', #basic.
             ['foo']),

             ('\n',
              ['']),   
             
             ('foo\\nbar\n', #multiple things on one input.
             ['foo', 'bar']),

             ('foo;bar\n', #semicolon linebreak this time
             ['foo', 'bar']),

             ('foo\\x0Abar\\012', #octal and hex escapes.
             ['foo', 'bar']),

             ('\\x57\n',
             ['\x57']),

             ('\\100\\10\\1\n',
             ['\100\10\1']),

             ('\\\\foo\n', #escaped backslashes.
             ['\\foo']),

             ('\\;bar\n', #escaped semicolons
             [';bar']),

             ('\\foo\n', #and unknown escapes.
             ['\\foo'])]
             
    error_tests = [('\\xoink\n', InvalidEscape),
                   ('bar\\', InvalidInput),
                   ('foo\\xb', InvalidEscape)]

    def test_normals(self):
        for test, expected in self.tests:
            yield self.do_one_normal, test, expected

    def do_one_normal(self, input, expected):
        res = list(self.eparser.parse(input))
        assert res == expected, res

    def run_error_tests(self):
        for test, err in self.error_tests:
        	yield self.do_one_error, test, err

    def do_one_error(self, input, expected_err):      
        try:
            res = list(self.eparser.parse(input))
        except expected_err: #I love Python so much. :)
            pass
        else:
        	assert False, res

    def test_retain_if_no_newline(self):
        res = list(self.eparser.parse('foo'))
        assert res == []
        res = list(self.eparser.parse('\n'))
        assert res == ['foo']

    def test_vanish_newline(self):
        res = list(self.eparser.parse('foo\\\n')) #backslash - newline
        assert res == []
        res = list(self.eparser.parse('\n'))
        assert res == ['foo']
    
    def test_chopped_octal_escape(self):
        res = list(self.eparser.parse('foo\\1'))
        assert res == []
        res = list(self.eparser.parse('\n'))
        assert res == ['foo\1']
