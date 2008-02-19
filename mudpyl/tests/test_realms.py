from mudpyl.realms import RootRealm
from mudpyl.colours import fg_code, bg_code, WHITE, BLACK, HexFGCode
from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.triggers import binding_trigger
from mudpyl.aliases import binding_alias
from mudpyl.net.telnet import TelnetClientFactory, TelnetClient
from mudpyl.output_manager import OutputManager
from mock import Mock
import time

class FooException(Exception):
    pass

class Bad:
    def __init__(self, c):
        raise FooException()

class Circular:
    def __init__(self, c):
        pass
Circular.modules = [Circular]

class WithTriggers:
    def __init__(self, c):
        c.triggers = [2, 1, 6, 3]
        c.aliases = [10, 4, 6, 9, 1, 2]
    modules = []

class TestModuleLoading:

    def setUp(self):
        self.c = RootRealm(None)

    def test_load_sorts_triggers_and_aliases(self):
        self.c.load_module(WithTriggers)
        assert self.c.triggers == [1, 2, 3, 6]
        assert self.c.aliases == [1, 2, 4, 6, 9, 10]

    def test_circular_requirements(self):
        self.c.load_module(Circular)
        assert self.c.modules_loaded == set([Circular])

    def test_removes_from_modules_loaded_on_error(self):
        try:
            self.c.load_module(Bad)
        except FooException:
            assert Bad not in self.c.modules_loaded
        else:
    	    assert False

#XXX: test clear_modules

class Test_write:

    def setUp(self):
        self.fore = "tata"
        self.back = "toto"
        self.fact = TelnetClientFactory(None, 'ascii', None)
        self.fact.outputs = Mock(spec = OutputManager)
        self.fact.outputs.fore = self.fore
        self.fact.outputs.back = self.back
        self.realm = self.fact.realm
        self.realm.telnet = Mock(spec = TelnetClient)
        #hack: use set() here because it has copy()
        self.noting_line = Metaline('foo', set(), set())

    def writer(self, match, realm):
        print 'writer called!'
        realm.write(self.noting_line)

    @property
    def lines_gotten(self):
        return [line for ((line,), kwargs) in 
                            self.fact.outputs.write_to_screen.call_args_list]

    def test_from_not_a_string(self):
        self.realm.write(42)
        assert len(self.lines_gotten) == 1
        assert self.lines_gotten[0].line == '42'

    def test_from_string(self):
        self.realm.write('spam')
        assert len(self.lines_gotten) == 1
        assert self.lines_gotten[0].line == 'spam'

    def test_from_metaline(self):
        ml = Metaline('foo', None, None)
        self.realm.write(ml)
        assert self.lines_gotten == [ml]

    def test_no_colourbleed_fg(self):
        self.realm.write("eggs")
        cols = self.lines_gotten[0].fores.as_pruned_index_list()
        expected = [(0, fg_code(WHITE, False))]
        assert cols == expected, (cols, expected)

    def test_no_colourbleed_bg(self):
        self.realm.write("eggs")
        cols = self.lines_gotten[0].backs.as_pruned_index_list()
        assert cols ==  [(0, bg_code(BLACK))], cols

    def test_passes_on_wrap_default(self):
        self.realm.write("eggs")
        assert not self.lines_gotten[0].wrap

    def test_soft_line_start_default_is_off(self):
        self.realm.write("barbaz")
        assert not self.lines_gotten[0].soft_line_start

    def test_passes_on_soft_line_start(self):
        self.realm.write('foo', soft_line_start = True)
        assert self.lines_gotten[0].soft_line_start

    noting_trigger = binding_trigger('bar')(writer)
    noting_alias = binding_alias('bar')(writer)

    def test_write_writes_after_during_matching_triggers(self):
        self.realm.triggers.append(self.noting_trigger)
        inline = Metaline('bar', set(), set())
        self.realm.receive(inline)
        assert self.lines_gotten == [inline, self.noting_line], \
               self.lines_gotten

    def test_write_writes_after_during_alias_matching(self):
        self.realm.aliases.append(self.noting_alias)
        inline = Metaline('bar', RunLengthList([(0, fg_code(WHITE, False))]),
                          RunLengthList([(0, bg_code(BLACK))]),
                          soft_line_start = True)
        self.realm.send('bar')
        print self.lines_gotten
        print
        expected = [inline, self.noting_line]
        print expected
        assert self.lines_gotten == expected

    def test_write_sends_peek_line(self):
        p = Mock()
        self.realm.add_peeker(p)
        self.realm.write('foobar')
        assert p.peek_line.call_args == (('foobar',), {})

class Test_receive:

    def setUp(self):
        self.fore = "tata"
        self.back = "toto"
        self.fact = TelnetClientFactory(None, 'ascii', None)
        self.fact.outputs = Mock(spec = OutputManager)
        self.fact.outputs.fore = self.fore
        self.fact.outputs.back = self.back
        self.realm = self.fact.realm
        self.ml = Metaline('foo', set(), set())
        self.ml2 = Metaline("bar", None, None)

    @property
    def lines_gotten(self):
        return [line for ((line,), kwargs) in 
                            self.fact.outputs.write_to_screen.call_args_list]

    def test_sends_to_screen_normally(self):
        self.realm.receive(self.ml)
        assert self.lines_gotten == [self.ml]

    @binding_trigger("foo")
    def trigger_1(self, match, realm):
        realm.write(self.ml2)

    def test_write_writes_afterwards(self):
        self.realm.triggers.append(self.trigger_1)
        self.realm.receive(self.ml)
        assert self.lines_gotten == [self.ml, self.ml2]

    @binding_trigger("foo")
    def trigger_2(self, match, realm):
        realm.display_line = False

    def test_doesnt_display_if_asked_not_to(self):
        self.realm.triggers.append(self.trigger_2)
        self.realm.receive(self.ml)
        assert self.lines_gotten == []

    @binding_alias("spam")
    def bar_writing_alias(self, match, realm):
        realm.write("BAR BAR BAR")
        realm.send_to_mud = False
    
    @binding_trigger('foo')
    def spam_sending_trigger(self, match, realm):
        realm.send("spam")

    def test_aliases_inside_triggers_write_after_trigger_writes(self):
        self.realm.triggers.append(self.spam_sending_trigger)
        self.realm.aliases.append(self.bar_writing_alias)

        noteline = Metaline("BAR BAR BAR",
                            RunLengthList([(0, fg_code(WHITE, False))]),
                            RunLengthList([(0, bg_code(BLACK))]))

        self.realm.receive(self.ml)

        assert self.lines_gotten == [self.ml, noteline]

    #XXX: test trigger matching specifically instead of accidentally

class Test_send:

    def setUp(self):
        self.fore = "tata"
        self.back = "toto"
        self.fact = TelnetClientFactory(None, 'ascii', None)
        self.fact.outputs = Mock(spec = OutputManager)
        self.fact.outputs.fore = self.fore
        self.fact.outputs.back = self.back
        self.realm = self.fact.realm
        self.realm.telnet = self.tc = Mock(spec = TelnetClient)

    @property
    def lines_gotten(self):
        return [line for ((line,), kwargs) in 
                            self.fact.outputs.write_to_screen.call_args_list]

    def test_send_sends_to_the_mud(self):
        self.realm.send("bar")
        assert self.tc.sendLine.call_args_list == [(('bar',), {})]

    def test_send_echos_by_default(self):
        self.realm.send("bar")
        expected = Metaline('bar', 
                            RunLengthList([(0, fg_code(WHITE, False))]),
                            RunLengthList([(0, bg_code(BLACK))]),
                            soft_line_start = True)
        assert self.lines_gotten == [expected]

    def test_send_doesnt_echo_if_told_not_to(self):
        self.realm.send("bar", False)
        assert self.lines_gotten == []

    def test_send_uses_echoes_with_soft_line_start(self):
        self.realm.send("spam")
        expected = Metaline('spam', 
                            RunLengthList([(0, fg_code(WHITE, False))]),
                            RunLengthList([(0, bg_code(BLACK))]),
                            soft_line_start = True)
        assert self.lines_gotten == [expected]

    #TODO: (not tested yet)
    #  - test calling send in a trigger and echoing then
    #  - test recursive calls to send properly
    #  - actually test matching properly

    @binding_alias("bar")
    def our_alias_1(self, match, realm):
        print 'sending after!'
        realm.send_after("foo")

    def test_send_after_sends_afterwards(self):
        self.realm.aliases.append(self.our_alias_1)
        self.realm.send('bar')

        assert self.tc.sendLine.call_args_list == [(('bar',), {}), 
                                                   (('foo',), {})]

    def test_send_after_default_echoing_is_off(self):
        self.realm.aliases.append(self.our_alias_1)
        self.realm.send("bar")
        expected = [Metaline('bar', 
                             RunLengthList([(0, fg_code(WHITE, False))]),
                             RunLengthList([(0, bg_code(BLACK))]),
                             soft_line_start = True)]
        assert self.lines_gotten == expected

    @binding_alias('baz')
    def our_alias_2(self, match, realm):
        realm.send_after("eggs", echo = False)

    def test_send_after_doesnt_echo_if_asked_not_to(self):
        self.realm.aliases.append(self.our_alias_2)
        self.realm.send("baz")
        expected = [Metaline('baz', 
                             RunLengthList([(0, fg_code(WHITE, False))]),
                             RunLengthList([(0, bg_code(BLACK))]),
                             soft_line_start = True)]
        assert self.lines_gotten == expected

    @binding_alias("foo")
    def foo_alias_sends_bar(self, match, realm):
        print 'Foo alias going!'
        realm.send('bar', echo = True)

    @binding_alias("bar")
    def bar_alias_sends_baz(self, match, realm):
        print 'Bar alias going'
        realm.send('baz', echo = True)

    def test_sends_and_writes_in_a_consistent_order(self):
        self.realm.aliases.append(self.foo_alias_sends_bar)
        self.realm.aliases.append(self.bar_alias_sends_baz)
        self.realm.send("foo", echo = True)

        expect_write = [Metaline("baz",
                                 RunLengthList([(0, fg_code(WHITE, False))]),
                                 RunLengthList([(0, bg_code(BLACK))]),
                                 soft_line_start = True),
                        Metaline("bar",
                                 RunLengthList([(0, fg_code(WHITE, False))]),
                                 RunLengthList([(0, bg_code(BLACK))]),
                                 soft_line_start = True),
                        Metaline("foo",
                                 RunLengthList([(0, fg_code(WHITE, False))]),
                                 RunLengthList([(0, bg_code(BLACK))]),
                                 soft_line_start = True)]
        expect_send = ['baz', 'bar', 'foo']
        sent = [line for ((line,), kwargs) in self.tc.sendLine.call_args_list]

        assert self.lines_gotten == expect_write
        assert sent == expect_send

    @binding_alias('spam')
    def noisy_alias(self, match, realm):
        realm.write("FOO FOO FOO")

    def test_writes_come_after_echoing(self):
        self.realm.aliases.append(self.noisy_alias)
        self.realm.send("spam")

        expecting = [Metaline("spam",
                              RunLengthList([(0, fg_code(WHITE, False))]),
                              RunLengthList([(0, bg_code(BLACK))]),
                              soft_line_start = True),
                     Metaline("FOO FOO FOO",
                              RunLengthList([(0, fg_code(WHITE, False))]),
                              RunLengthList([(0, bg_code(BLACK))]))]

        assert self.lines_gotten == expecting
                              
#XXX: not tested still - TriggerMatchingRealm
#also not tested: send() and default echoing in MatchingRealms

from mudpyl.gui.bindings import gui_macros

class TestOtherStuff:

    def setUp(self):
        self.realm = RootRealm(None)
        self.realm.telnet = self.telnet = Mock(spec = TelnetClient)
    
    def test_ga_as_line_end_is_defaultly_True(self):
        assert self.realm.ga_as_line_end

    def test_close_closes_telnet(self):
        self.realm.close()
        assert self.telnet.close.called

    def test_close_clears_telnet_attribute(self):
        self.realm.close()
        assert self.realm.telnet is None

    def test_close_is_a_noop_when_telnet_is_None(self):
        self.realm.telnet = None
        self.realm.close()
        assert self.realm.telnet is None

    def test_gui_macros_are_defaultly_loaded(self):
        assert self.realm.macros == gui_macros

    def test_baked_in_macros_loaded_after_clear(self):
        self.realm.baked_in_macros['f'] = 'foo'
        self.realm.clear_modules()
        res = gui_macros.copy()
        res['f'] = 'foo'
        assert self.realm.macros == res

#XXX: test clear_modules

from mudpyl.gui.keychords import from_string
from mock import patch

class Test_maybe_do_macro:

    def setUp(self):
        self.realm = RootRealm(None)
        self.realm.macros[from_string('X')] = self.macro
        self.realm.macros[from_string('C-M-X')] = self.bad_macro
        self.realm.macros[from_string('Z')] = self.simulated_grumpy_user
        self.realm.macros[from_string('L')] = self.macro_returning_true
        self.macro_called_with = []

    def macro(self, realm):
        self.macro_called_with.append(realm)

    def macro_returning_true(self, realm):
        self.macro_called_with.append(realm)
        return True

    def bad_macro(self, realm):
        raise Exception

    def simulated_grumpy_user(self, realm):
        raise KeyboardInterrupt

    def test_returns_False_if_no_macro_found(self):
        res = self.realm.maybe_do_macro(from_string('Q'))
        assert not res

    def test_returns_True_if_a_macro_found(self):
        res = self.realm.maybe_do_macro(from_string('X'))
        assert res

    def test_calls_macro_with_itself(self):
        self.realm.maybe_do_macro(from_string('X'))
        assert len(self.macro_called_with) == 1
        assert self.macro_called_with[0] is self.realm

    def test_KeyboardInterrupt_is_not_caught(self):
        try:
            self.realm.maybe_do_macro(from_string('Z'))
        except KeyboardInterrupt:
            pass
        else:
            assert False

    @patch('mudpyl.realms', 'traceback')
    def test_Exception_is_caught(self, tb):
        self.realm.maybe_do_macro(from_string('C-M-X'))
        assert tb.print_exc.called

    @patch('mudpyl.realms', 'traceback')
    def test_bad_macros_still_return_True(self, tb):
        res = self.realm.maybe_do_macro(from_string('C-M-X'))
        assert res

    def test_macro_that_returns_True_tells_gui_to_keep_processing(self):
        res = self.realm.maybe_do_macro(from_string('L'))
        assert not res

class Test_connection_events:

    def setUp(self):
        self.factory = TelnetClientFactory(None, 'ascii', None)
        self.realm = RootRealm(self.factory)
        self.realm.telnet = self.telnet = Mock(spec = TelnetClient)
        self.receiver = Mock()
        self.realm.add_connection_receiver(self.receiver)

    def test_passes_on_connection_lost(self):
        self.realm.connection_lost()
        assert self.receiver.connection_lost.called

    @patch('mudpyl.realms', 'time')
    def test_connection_lost_writes_message(self, our_time):
        our_time.strftime.return_value = 'FOOBAR'
        self.realm.write = Mock()
        self.realm.connection_lost()
        assert self.realm.write.called
        ml = self.realm.write.call_args[0][0]
        assert ml.line == 'FOOBAR'
        assert ml.fores.as_populated_list() == [HexFGCode(0xFF, 0xAA, 0x00)]
        assert ml.backs.as_populated_list() == [bg_code(BLACK)]

    @patch('mudpyl.realms', 'time')
    def test_connection_made_writes_message(self, our_time):
        our_time.strftime.return_value = 'FOOBAR'
        self.realm.write = Mock()
        self.realm.connection_made()
        assert self.realm.write.called
        ml = self.realm.write.call_args[0][0]
        assert ml.line == 'FOOBAR'
        assert ml.fores.as_populated_list() == [HexFGCode(0xFF, 0xAA, 0x00)]
        assert ml.backs.as_populated_list() == [bg_code(BLACK)]

    def test_passes_on_connection_made(self):
        self.realm.connection_made()
        assert self.receiver.connection_made.called

    def test_sends_connection_lost_and_close_in_right_order(self):
        self.realm.close()
        #simulate Twisted's 'throw-it-over-the-wall' anti-guarantee
        self.realm.connection_lost()
        calls = [mname for (mname, args, kws) in self.receiver.method_calls]
        assert calls == ['connection_lost', 'close']

    def test_connection_lost_then_close_works(self):
        self.realm.connection_lost()
        self.realm.close()
        calls = [mname for (mname, args, kws) in self.receiver.method_calls]
        assert calls == ['connection_lost', 'close']

    def test_connection_lost_sets_telnet_to_None(self):
        self.realm.connection_lost()
        assert self.realm.telnet is None

from mudpyl.modules import load_file

class DummyModule:

    triggers = []
    aliases = []
    macros = {}
    modules = []

    def __init__(self, realm):
        pass

from mock import sentinel

class Test_reload:

    def setUp(self):
        self.factory = TelnetClientFactory(None, None, sentinel.ModuleName)
        self.realm = RootRealm(self.factory)

    @patch('mudpyl.realms', 'load_file')
    def test_calls_load_file(self, our_load_file):
        our_load_file.return_value = DummyModule
        self.realm.reload_main_module()
        assert our_load_file.called

    @patch('mudpyl.realms', 'load_file')
    def test_calls_load_file_with_main_module_name(self, our_load_file):
        our_load_file.return_value = DummyModule
        self.realm.reload_main_module()
        assert our_load_file.call_args[0] == (sentinel.ModuleName,)

    @patch('mudpyl.realms', 'load_file')
    def test_clears_modules(self, our_load_file):
        our_load_file.return_value = DummyModule
        self.realm.clear_modules = Mock()
        self.realm.reload_main_module()
        assert self.realm.clear_modules.called

    @patch('mudpyl.realms', 'load_file')
    def test_calls_load_module(self, our_load_file):
        our_load_file.return_value = sentinel.Module
        self.realm.load_module = Mock()
        self.realm.reload_main_module()
        assert self.realm.load_module.called
        assert self.realm.load_module.call_args[0] == (sentinel.Module,)
