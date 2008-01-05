from mudpyl.gui.commandhistory import CommandHistory

class TestCommandHistory:

    def setUp(self):
        self.c = CommandHistory(5)

    def test_adds_new_command_to_buffer(self):
        self.c.add_command("foo")
        r = self.c.advance()
        assert r == 'foo', r

    def test_doesnt_add_dupes(self):
        self.c.add_command("spam")
        self.c.add_command("foo")
        self.c.add_command("foo")
        assert self.c.advance() == 'foo'
        assert self.c.advance() == 'spam'

    def test_is_LIFO_wrt_commands(self):
        self.c.add_command("foo")
        self.c.add_command('bar')
        self.c.add_command("baz")
        assert self.c.advance() == 'baz'
        assert self.c.advance() == 'bar'
        assert self.c.advance() == 'foo'

    def test_doesnt_add_blanks_to_history(self):
        self.c.add_command("foo")
        self.c.add_command(" ")
        assert self.c.advance() == 'foo'

    def test_has_maximum_buffer_size(self):
        cs = 'foo bar baz qux spam eggs'.split()
        for c in cs:
            self.c.add_command(c)
        res = [self.c.advance() for _ in range(6)]
        assert res == ['eggs', 'spam', 'qux', 'baz', 'bar', 'bar'], res

    def test_moving_back_and_forth(self):
        for c in reversed('foo bar baz spam eggs'.split()):
            self.c.add_command(c)
        assert self.c.advance() == 'foo'
        assert self.c.advance() == 'bar'
        assert self.c.advance() == 'baz'
        assert self.c.retreat() == 'bar'

    def test_goes_back_to_start_on_normal_addition(self):
        self.c.add_command("foo")
        self.c.add_command("bar")
        self.c.advance()
        self.c.add_command('baz')
        assert self.c.advance() == 'baz'

    def test_goes_back_to_start_on_blank(self):
        self.c.add_command('foo')
        self.c.add_command('baz')
        self.c.advance()
        self.c.add_command("")
        assert self.c.advance() == 'baz'

    def test_no_strange_stuff_on_bogus_retreat(self):
        self.c.add_command("foo")
        self.c.add_command("bar")
        self.c.add_command("baz")
        assert self.c.retreat() == ''

    def test_advance_with_empty_buffer_reutrns_empty_string(self):
        assert self.c.advance() == ''
