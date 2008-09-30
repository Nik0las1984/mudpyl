from mudpyl.modules import load_file, EarlyInitialisingModule, BaseModule
import sys
from mock import patch, sentinel, Mock

class _ModuleTest:
    def test_default_is_main_exists(self):
        self.cls(Mock()).is_main(Mock())

    def test_encoding_is_defaultly_utf_8(self):
        assert self.cls.encoding == 'utf-8'

    def test_sets_manager_as_first_argument(self):
        m = Mock()
        assert self.cls(m).manager is m

def our_import(name, globals, locals, importlist):
    if name == 'foobar' and importlist == ['MainModule']:
        m = Mock()
        m.MainModule = sentinel.Module
        return m

@patch('__builtin__', '__import__', our_import)
def test_load_file_loads_script():
    m = load_file("foobar")
    assert m == sentinel.Module

def test_load_file_reimports():
    sys.modules["foobar"] = object()
    test_load_file_loads_script()

class TestBaseModule(_ModuleTest):
    cls = BaseModule

    def test_adds_triggers_aliases_and_macros(self):
        class Module(self.cls):
            trigger = object()
            triggers = [trigger]
            alias = object()
            aliases = [alias]
            macro = object()
            macros = {'f': macro}

        manager = Mock()
        manager.triggers = []
        manager.aliases = []
        manager.macros = {}
        Module(manager)

        assert len(manager.triggers) == 1
        assert manager.triggers[0] is Module.trigger
        assert len(manager.aliases) == 1
        assert manager.aliases[0] is Module.alias
        assert len(manager.macros) == 1
        assert manager.macros['f'] is Module.macro

class TestEarlyInitialisingModule(_ModuleTest):
    cls = EarlyInitialisingModule()

    def test_adds_triggers_aliases_and_macros(self):
        class Module(EarlyInitialisingModule):
            trigger = object()
            triggers = [trigger]
            alias = object()
            aliases = [alias]
            macro = object()
            macros = {'f': macro}

        manager = Mock()
        manager.triggers = []
        manager.aliases = []
        manager.macros = {}
        Module()(manager)

        assert len(manager.triggers) == 1
        assert manager.triggers[0] is Module.trigger
        assert len(manager.aliases) == 1
        assert manager.aliases[0] is Module.alias
        assert len(manager.macros) == 1
        assert manager.macros['f'] is Module.macro
