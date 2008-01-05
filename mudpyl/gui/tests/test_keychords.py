from mudpyl.gui.keychords import from_string, InvalidSpecialKeyError, \
                                 CantParseThatError, InvalidModifiersError

#XXX: need to make all the wx-dependent tests conditional on importing wx

def single_keychord_key_equal(key, chord):
    assert chord.key == key

def test_special_keys_go_through_alright():
    allowed_specials = ["backspace", 
                        "tab", 
                        "return",
                        "enter",
                        "dash",
                        "pause",
                        "escape",
                        "page up",
                        "page down",
                        "end",
                        "home",
                        "left",
                        "up",
                        "right",
                        "down", 
                        "insert",
                        "delete"] + \
                        ['f%d' % n for n in range(1, 13)] + \
                        ['numpad %s' % n for n in range(0, 10) +
                                                  ['add', 'divide', 
                                                   'multiply', 'subtract']]

    for special in allowed_specials:
        yield single_keychord_key_equal, special, from_string('<%s>' % special)

def test_invalid_special_keys_raises_errors():
    invalid_specials = ['foo', 'bar', 'baz']

    for special in invalid_specials:
        try:
            v = from_string('<%s>')
        except InvalidSpecialKeyError:
            pass
        else:
            assert False, v

def test_case_insensitivity_in_special_keys():
    vals = ['escape', 'EsCaPe', 'esCApe', 'ESCAPE']

    for val in vals:
        yield single_keychord_key_equal, 'escape', from_string('<%s>' % val)

def test_blows_up_on_unclosed_special_key():
    try:
        res = from_string('<escape')
    except CantParseThatError:
        pass
    else:
        assert False, res

def test_blows_up_on_unexpected_sequence_of_characters():
    try:
        res = from_string('foo')
    except CantParseThatError:
        pass
    else:
        assert False, res

def test_normal_key_setting():
    assert from_string('f').key == 'f'

def test_normal_key_case_insensitive():
    assert from_string('F').key == 'f'

def test_modifiers_are_case_sensitive():
    try:
        res = from_string('m-f')
    except InvalidModifiersError:
        pass
    else:
        assert False

def test_rejects_unknown_modifier():
    try:
        res = from_string('x-f')
    except InvalidModifiersError:
        pass
    else:
        assert False

def test_rejects_blank_key():
    try:
        res = from_string('')
    except CantParseThatError:
        pass
    else:
        assert False

def test_rejects_blank_key_with_modifier():
    try:
        res = from_string('M-')
    except CantParseThatError:
        pass
    else:
        assert False

def test_rejects_dash_on_its_own():
    try:
        res = from_string('-')
    except (InvalidModifiersError, CantParseThatError):
        pass
    else:
        assert False

def test_sets_Control_key_to_true():
    assert from_string('C-f').control

def test_control_key_flag_is_default_false():
    assert not from_string('f').control

def test_alt_key_flag_is_default_false():
    assert not from_string('f').meta

def test_alt_key_setting_to_true():
    assert from_string('M-f').meta

def test_alt_and_control_work_together():
    c = from_string('C-M-f')
    assert c.meta and c.control

def test_ordering_of_modifiers_doesnt_matter():
    c1 = from_string('C-M-q')
    c2 = from_string('M-C-q')
    assert c1 == c2

def test_equality():
    #XXX: other interesting comparison cases
    kc1 = from_string('f')
    kc2 = from_string('f')
    assert kc1 == kc2, (kc1, kc2)

def test_KeyChord_unicode_and_ascii_characters_are_the_same():
    kc1 = from_string('f')
    kc2 = from_string(u'f')
    assert kc1 == kc2

def test_inequality():
    assert from_string('m') != from_string('r')

def test_equal_chords_hash_the_same():
    assert hash(from_string('f')) == hash(from_string('f'))

import wx
from mudpyl.gui.keychords import from_wx_event

class MockEvent:

    def __init__(self, control, alt, code):
        self.control = control
        self.alt = alt
        self.code = code

    def ControlDown(self):
        return self.control

    def AltDown(self):
        return self.alt

    def GetKeyCode(self):
        return self.code
    KeyCode = property(GetKeyCode)

def test_creates_KeyChords_from_wx_events_with_ASCII_keys():
    ev = MockEvent(False, False, ord('a'))
    c = from_wx_event(ev)
    assert c == from_string('a')

def test_from_wx_event_puts_control_through_properly():
    ev = MockEvent(True, False, ord('a'))
    c = from_wx_event(ev)
    assert c == from_string('C-a')

def test_from_wx_event_puts_meta_through_properly():
    ev = MockEvent(False, True, ord('a'))
    c = from_wx_event(ev)
    assert c == from_string('M-a')

corres =  {"backspace": 8,
           "tab": wx.WXK_TAB,
           "return": wx.WXK_RETURN,
           "enter": wx.WXK_NUMPAD_ENTER,
           "dash": ord('-'),
           "pause": wx.WXK_PAUSE,
           "escape": wx.WXK_ESCAPE,
           "page up": wx.WXK_PAGEDOWN,
           "page down": wx.WXK_PAGEUP,
           "end": wx.WXK_END,
           "home": wx.WXK_HOME,
           "left": wx.WXK_LEFT,
           "up": wx.WXK_UP,
           "right": wx.WXK_RIGHT,
           "down": wx.WXK_DOWN, 
           "insert": wx.WXK_INSERT,
           "delete": wx.WXK_DELETE,
           'f1': wx.WXK_F1,
           'f2': wx.WXK_F2,
           'f3': wx.WXK_F3,
           'f4': wx.WXK_F4,
           'f5': wx.WXK_F5,
           'f6': wx.WXK_F6,
           'f7': wx.WXK_F7,
           'f8': wx.WXK_F8,
           'f9': wx.WXK_F9,
           'f10': wx.WXK_F10,
           'f11': wx.WXK_F11,
           'f12': wx.WXK_F12,
           'numpad 1': wx.WXK_NUMPAD1,
           'numpad 2': wx.WXK_NUMPAD2,
           'numpad 3': wx.WXK_NUMPAD3,
           'numpad 4': wx.WXK_NUMPAD4,
           'numpad 5': wx.WXK_NUMPAD5,
           'numpad 6': wx.WXK_NUMPAD6,
           'numpad 7': wx.WXK_NUMPAD7,
           'numpad 8': wx.WXK_NUMPAD8,
           'numpad 9': wx.WXK_NUMPAD9,
           'numpad 0': wx.WXK_NUMPAD0,
           'numpad add': wx.WXK_NUMPAD_ADD,
           'numpad divide': wx.WXK_NUMPAD_DIVIDE,
           'numpad subtract': wx.WXK_NUMPAD_SUBTRACT,
           'numpad multiply': wx.WXK_NUMPAD_MULTIPLY}

def one_comparison(our_name, wx_code):
    assert from_wx_event(MockEvent(False, False, wx_code)) == \
           from_string('<%s>' % our_name)

def test_from_wx_event_converts_special_keys():
    for ours, theirs in corres.items():
        yield one_comparison, ours, theirs

from mudpyl.gui.keychords import KeyChord

def test_from_wx_event_unrecognised_code():
    ev = MockEvent(False, False, 538)
    assert from_wx_event(ev) == KeyChord(unichr(538), False, False)

def test_plays_nice_with_dict():
    d = {from_string('C-f'): 'foo',
         from_string('M-f'): 'bar',
         from_string('f'): 'baz'}
    assert from_string('C-f') in d
    assert d[from_string('M-f')] == 'bar'
