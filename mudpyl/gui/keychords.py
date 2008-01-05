"""A keychord representation system."""

#NOTE: the key pressed is case insensitive as far as macros are concerned. 
#C-T and C-t are the same key, but only C-T will be looked up.
#XXX: make macros case sensitive, perhaps? "S-"?
class KeyChord(object):
    """Represents one key with control and meta keys, possibly."""
    def __init__(self, key, control, meta):
        self.key = key
        self.control = control
        self.meta = meta

    def __eq__(self, other):
        return self.key == other.key and self.control == other.control and \
               self.meta == other.meta

    def __hash__(self):
        return hash(self.key) ^ hash(str(self.control)) ^ hash(str(self.meta))

    def __str__(self):
        return 'KeyChord(%r, %s, %s)' % (self.key, self.control, self.meta)
    __repr__ = __str__

legal_specials = ['backspace', 'tab', 'return', 'enter', 'dash', 
                  'pause', 'escape', 'page up', 'page down', 'end', 'home', 
                  'left', 'up', 'right', 'down', 'insert', 'delete', 
                  'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10',
                  'f11', 'f12', 'numpad 0', 'numpad 1', 'numpad 2', 
                  'numpad 3', 'numpad 4', 'numpad 5', 'numpad 6', 'numpad 7', 
                  'numpad 8', 'numpad 9', 'numpad add', 'numpad divide',
                  'numpad multiply', 'numpad subtract']


def from_string(string):
    """Converts a string representation of a chord into a KeyChord object.

    Example:
        >>> from_string("C-<enter>")
        KeyChord('enter', True, False)
    """
    parts = string.split('-')
    key = parts.pop(-1).lower()
    
    modifiers = set(parts)
    control = 'C' in modifiers
    meta = 'M' in modifiers
    if modifiers - set('CM'):
    	#illegal things in front.
        raise InvalidModifiersError

    if len(key) > 1:
        if not key.startswith('<') or not key.endswith('>'):
            raise CantParseThatError(key)
        #strip angle brackets
        key = key[1:-1]
        if key not in legal_specials:
            raise InvalidSpecialKeyError(key)
    elif not key:
        raise CantParseThatError("Blank key")

    return KeyChord(key, control, meta)

try:
    import wx
except ImportError:
    pass
else:
    wx_codes =  {8: "backspace",
                 wx.WXK_TAB: 'tab',
                 wx.WXK_RETURN: "return",
                 wx.WXK_NUMPAD_ENTER: "enter",
                 ord('-'): "dash",
                 wx.WXK_PAUSE: "pause",
                 wx.WXK_ESCAPE: "escape",
                 wx.WXK_PAGEDOWN: "page up",
                 wx.WXK_PAGEUP: "page down",
                 wx.WXK_END: "end",
                 wx.WXK_HOME: "home",
                 wx.WXK_LEFT: "left",
                 wx.WXK_UP: "up",
                 wx.WXK_RIGHT: "right",
                 wx.WXK_DOWN: "down",
                 wx.WXK_INSERT: "insert",
                 wx.WXK_DELETE: "delete",
                 wx.WXK_F1: 'f1',
                 wx.WXK_F2: 'f2',
                 wx.WXK_F3: 'f3',
                 wx.WXK_F4: 'f4',
                 wx.WXK_F5: 'f5',
                 wx.WXK_F6: 'f6',
                 wx.WXK_F7: 'f7',
                 wx.WXK_F8: 'f8',
                 wx.WXK_F9: 'f9',
                 wx.WXK_F10: 'f10',
                 wx.WXK_F11: 'f11',
                 wx.WXK_F12: 'f12',
                 wx.WXK_NUMPAD1: 'numpad 1',
                 wx.WXK_NUMPAD2: 'numpad 2',
                 wx.WXK_NUMPAD3: 'numpad 3',
                 wx.WXK_NUMPAD4: 'numpad 4',
                 wx.WXK_NUMPAD5: 'numpad 5',
                 wx.WXK_NUMPAD6: 'numpad 6',
                 wx.WXK_NUMPAD7: 'numpad 7',
                 wx.WXK_NUMPAD8: 'numpad 8',
                 wx.WXK_NUMPAD9: 'numpad 9',
                 wx.WXK_NUMPAD0: 'numpad 0',
                 wx.WXK_NUMPAD_ADD: 'numpad add',
                 wx.WXK_NUMPAD_DIVIDE: 'numpad divide',
                 wx.WXK_NUMPAD_SUBTRACT: 'numpad subtract',
                 wx.WXK_NUMPAD_MULTIPLY: 'numpad multiply'}

    def from_wx_event(event):
        """Convert a wx.KeyEvent to a KeyChord."""
        try:
            #see if it's a special code   
            code = wx_codes[event.KeyCode]
        except KeyError:
            #otherwise, it's a boring ASCII character or something we don't 
            #know about. There are some wx keycodes we don't know about, and 
            #which ASCII-only chr() would blow up on, so use unichr as a 
            #workaround.
            code = unichr(event.KeyCode)
        return KeyChord(code, event.ControlDown(), event.AltDown())

try:
    import gtk
except ImportError:
    pass
else:
    unusual_gtk_codes = {'kp_enter': 'enter',
                         'kp_1': 'numpad 1',
                         'kp_2': 'numpad 2',
                         'kp_3': 'numpad 3',
                         'kp_4': 'numpad 4',
                         'kp_5': 'numpad 5',
                         'kp_6': 'numpad 6',
                         'kp_7': 'numpad 7',
                         'kp_8': 'numpad 8',
                         'kp_9': 'numpad 9',
                         'kp_0': 'numpad 0',
                         'kp_divide': 'numpad divide',
                         'kp_multiply': 'numpad multiply',
                         'kp_subtract': 'numpad subtract',
                         'kp_add': 'numpad add',
                         'page_up': 'page up',
                         'page_down': 'page down',
                         'minus': 'dash'}

    def from_gtk_event(event):
        """Turn GTK's key-press-event into a KeyChord."""
        name = gtk.gdk.keyval_name(event.keyval).lower()

        #GTK and us share a few common names, so we only look up where it's
        #different. These may differ in case than ours, which is why we do
        #.lower() above.
        if name in unusual_gtk_codes:
        	name = unusual_gtk_codes[name]
        #though this isn't a special key we care about. Might be out of
        #ASCII bounds, though, so use unichr. Catching Caps_Lock and company
        #is a feature, not a bug (for now). GTK does capital-conversion
        #before we get a peek at the key, so we uppercase it.
        elif not name in legal_specials:
            name = unichr(event.keyval).upper()

        meta = bool(event.state & gtk.gdk.MOD1_MASK)
        control = bool(event.state & gtk.gdk.CONTROL_MASK)

        return KeyChord(name, control, meta)

class InvalidModifiersError(Exception):
    """An unrecognised modifier was used."""
    pass

class InvalidSpecialKeyError(Exception):
    """An invalid special key name was used."""
    pass

class CantParseThatError(Exception):
    """A general keychord parsing error occurred."""
    pass
