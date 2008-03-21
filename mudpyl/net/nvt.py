"""This module contains tools for emulating a network virtual terminal. See
RFC 854 for details of the NVT commands, and VT100 documentation for the 
colour codes.
"""
from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.colours import NORMAL_CODES, fg_code, bg_code, WHITE, BLACK
import re

ALL_RESET = '0'
BOLDON = '1'
BOLDOFF = '22'

FG_FLAG = '3'
BG_FLAG = '4'

GROUND_RESET = '8'

colour_pattern = re.compile( "\x1b" + #ESC
                            r"\[" #open square bracket
                            r"(\d+" #open group, initial digits
                            r"(?:;\d{1,2})*" #following digits
                            r")" #close the group
                             "m" #just an 'm'
                             )

toremove = set('\000' #NUL
               '\007' #BEL
               '\013' #VT
               '\014') #FF

BS = '\010'

HT = '\011' #AKA '\t' and tab.
HT_replacement = '    ' #four spaces

def make_string_sane(string):
    """Process (in most cases, this means 'ignore') the NVT characters in the
    input string.
    """
    #simple characters don't need any special machinery.
    for char in toremove:
        string = string.replace(char, '')
    #do it backspace by backspace because otherwise, if there were multiple 
    #backspaces in a row, it gets confused and backspaces over backspaces.
    while BS in string:
        #take off leading backspaces so that the following regex doesn't get 
        #confused.
        string = string.lstrip(BS)
        string = re.sub('.' + BS, '', string, 1)
    #swap tabs for four whitespaces.
    string = string.replace(HT, HT_replacement)
    return string

class ColourCodeParser(object):

    """A stateful colour code parser."""

    def __init__(self):
        self.fore = WHITE
        self.back = BLACK
        self.bold = False
    _reset = __init__

    def _parseline(self, line):
        """Feed it lines of VT100-infested text, and it splits it all up.
        
        This returns a threeple: a string, the foreground colours, and the
        background colours. The string is simple enough. The background list
        is a list of integers corresponding to WHITE, GREEN, etc. The
        foreground list is made up of two-ples: the first is the integer
        colour, and the second is whether bold is on or off.
        """
        backs = [(0, self.back)]
        fores = [(0, (self.fore, self.bold))]
        text = ''
        prev_end = 0
        
        for match in colour_pattern.finditer(line):
            text += line[prev_end:match.start()]
            prev_end = match.end()
            codes = match.group(1)

            for code in codes.split(';'):
                code = str(int(code, 10)) #normalisation.
                if code == ALL_RESET:
                    self._reset()
                    fores.append((len(text), self.get_fore()))
                    backs.append((len(text), self.back))
                elif code == BOLDON:
                    self.bold = True
                    fores.append((len(text), self.get_fore()))
                elif code == BOLDOFF:
                    self.bold = False
                    fores.append((len(text), self.get_fore()))

                elif code.startswith(FG_FLAG):
                    code = code[1:]
                    if code == GROUND_RESET:
                        code = WHITE
                    if code in NORMAL_CODES:
                        self.fore = code
                        fores.append((len(text), self.get_fore()))

                elif code.startswith(BG_FLAG):
                    code = code[1:]
                    if code == GROUND_RESET:
                        code = BLACK
                    if code in NORMAL_CODES:
                        self.back = code
                        backs.append((len(text), self.back))
        
        #We don't really care about chopped colour codes. This class is
        #actually going to be tossed whole lines (ie, \r\n or similar
        #terminated), and any escape code of the form "\x1b[\r\n30m" or
        #similar is broken anyway. I'll probably be proved wrong somehow
        #on this one...
        if len(line) - 1 > prev_end:
            text += line[prev_end:]

        return (fores, backs, text)

    def get_fore(self):
        """Return what the current foreground tuple is."""
        return self.fore, self.bold

    def parseline(self, line):
        """Interpret the VT100 codes in line and returns a Metaline, replete
        with RunLengthLists, that splits the text, foreground and background
        into three separate channels.
        """
        fores, backs, cleanline = self._parseline(line)
        rlfores = RunLengthList((length, fg_code(colour, bold))
                                for (length, (colour, bold)) in fores)
        rlbacks = RunLengthList((length, bg_code(colour))
                                for (length, colour) in backs)
        return Metaline(cleanline, rlfores, rlbacks)

