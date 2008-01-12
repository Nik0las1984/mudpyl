from mudpyl.modules import BaseModule
from mudpyl.net.telnet import TelnetClientFactory
from mudpyl.gui.bindings import gui_macros

def test_BaseModule_adds_triggers_aliases_and_macros():
    class Module(BaseModule):
        trigger = object()
        triggers = [trigger]
        alias = object()
        aliases = [alias]
        macro = object()
        macros = {'f': macro}

    f = TelnetClientFactory(None)
    Module(f.realm)

    assert len(f.realm.triggers) == 1
    assert f.realm.triggers[0] is Module.trigger
    assert len(f.realm.aliases) == 1
    assert f.realm.aliases[0] is Module.alias
    assert len(f.realm.macros) == 1 + len(gui_macros)
    assert f.realm.macros['f'] is Module.macro

from mudpyl.modules import load_file
import sys

class FakeMainModule:

    modules = []

    def __init__(self, clientfactory):
        clientfactory.loaded = True

class FakePythonModule:
    MainModule = FakeMainModule

def our_import(name, globals, locals, importlist):
    if name == 'foobar' and importlist == ['MainModule']:
        return FakePythonModule()

def test_load_file_loads_script():
    from mudpyl import modules
    modules.__import__ = our_import
    m = load_file("foobar")
    assert m is FakeMainModule

def test_load_file_reimports():
    sys.modules["foobar"] = object()
    test_load_file_loads_script()

