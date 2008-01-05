"""Classes and constants for representing colours."""
BLACK = '0'
RED = '1'
GREEN = '2'
YELLOW = '3'
BLUE = '4'
PURPLE = '5'
CYAN = '6'
WHITE = '7'

NORMAL_CODES = set([BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE])

normal_colours = {BLACK: (0x00, 0x00, 0x00),
                  RED: (0x80, 0x00, 0x00),
                  GREEN: (0x00, 0x80, 0x00),
                  YELLOW: (0x80, 0x80, 0x00),
                  BLUE: (0x36, 0x3A, 0xEB),
                  PURPLE: (0x80, 0x00, 0x80),
                  CYAN: (0x00, 0x61, 0x61),
                  WHITE: (0xC0, 0xC0, 0xC0)}

bolded_colours = {BLACK: (0x80, 0x80, 0x80),
                  RED: (0xFF, 0x00, 0x00),
                  GREEN: (0x00, 0xFF, 0x00),
                  YELLOW: (0xFF, 0xFF, 0x00),
                  BLUE: (0x81, 0x81, 0xFF),
                  PURPLE: (0xFF, 0x00, 0xFF),
                  CYAN: (0x00, 0xFF, 0xFF),
                  WHITE: (0xFF, 0xFF, 0xFF)}

def fg_code(code, bold):
    """Wrapper to convert a VT100 colour code to a HexFGCode."""
    if bold:
        dictionary = bolded_colours
    else:
        dictionary = normal_colours
    return HexFGCode(*dictionary[code])

def bg_code(code):
    """Wrapper to convert a VT100 colour code to a HexBGCode."""
    return HexBGCode(*normal_colours[code])

class _HexCode(object):
    """Base class for hex colour codes.
    
    The colour attributes are in the range 0..255, where 0 is absent and 255
    is brightest.
    """

    __slots__ = ['red', 'green', 'blue']

    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

    def __eq__(self, other):
        return type(self) == type(other) and self.triple == other.triple

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.tohex())

    def __hash__(self):
        return hash(type(self)) ^ hash(self.triple)

    @property
    def triple(self):
        """Wrap ourselves up as a handy tuple."""
        return self.red, self.green, self.blue
    
    def tohex(self):
        """Change a colour represented as a triple to a text representation.

        Suitable for embedding the colours into HTML.
        """
        return ''.join(('%x' % num).zfill(2) for num in self.triple)

class HexBGCode(_HexCode):
    """A hex background colour."""
    pass

class HexFGCode(_HexCode):
    """A hex foreground colour."""
    pass

