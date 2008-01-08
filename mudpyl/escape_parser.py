"""This module contains a utility for parsing strings with backslash-escapes 
in them, as well as a few other interesting characters.
"""
from collections import deque

class ParsingError(Exception):
    '''String parsing error. Base class.'''
    pass

class InvalidInput(ParsingError):
    '''The input's format was unuseable in some way.'''
    pass

class InvalidEscape(ParsingError):
    '''A user-entered escape was bad.'''
    pass

OCTDIGITS = '01234567'

class EscapeParser(object):
    """Turns backslash-escaped sequences into their characters, and splits the
    string at newlines and semicolons.
    """

    def __init__(self):
        self.buffer = deque()
        self.res = ''

    def handle_backslash(self):
        '''Process the backslash and the character it escapes.

        This returns a boolean value, signifying whether the buffer represents
        a complete line and so should be yielded.

        Note: on error, this throws away the whole input, to be on the safe
        side.
        '''
        try:
            char = self.buffer.popleft()
        except IndexError:
            raise InvalidInput("Backslash at the end of line and no newline")
        
        if char == 'n':
            #newline; return True because this needs to yield the contents of
            #the buffer
            return True
        elif char in ';\\':
            #escaped semicolon or backslash
            self.res += char
        elif char == 'x':
            #hex-encoded ASCII character
            return self.dohexdigits()
        elif char in OCTDIGITS:
            #octal-encoded ASCII character
            chars = char + self.getoctdigits()
            return self.handle_normal_char(chr(int(chars, 8)))
        elif char == '\n':        
            #actual newline characters always flush the buffer, but they also
            #preserve the backslash
            self.res += '\\'
            return True
        else:
            self.res += '\\%s' % char

        return False

    def handle_normal_char(self, char):
        '''Handle a normal character, with no (very) special semantics.'''
        if char == '\n':
            return True
        else:
            self.res += char
            return False

    def dohexdigits(self):
        '''Gets the next two chars, converts them to hex and puts them on the
        result.

        Note that this is a very fussy function.
        '''
        try:
            chars = self.buffer.popleft() + self.buffer.popleft()
        except IndexError:
            raise InvalidEscape('Bad \\x escape (not enough operands).')
        try:
            char = chr(int(chars, 16))
        except:
            raise InvalidEscape('Bad \\x escape (couldn\'t parse number).')
        return self.handle_normal_char(char)

    def getoctdigit(self):
        '''Get the next char if it's an octal digit, or an empty string if it 
        isn't.
        '''
        if not self.buffer or self.buffer[0] not in OCTDIGITS:
            return ''
        char = self.buffer.popleft()
        return char

    def getoctdigits(self):
        """Return up to a pair of octal digits."""
        return self.getoctdigit() + self.getoctdigit()

    def parse(self, string):
        '''Parse the string, returns an iterator yielding str results.

        The string fed to this function needs to have its input end in a
        newline, else it won't get flushed out.
        '''
        self.buffer.extend(string)
        
        while self.buffer:
            char = self.buffer.popleft()
            need_to_yield = False

            if char == '\\':
                try:
                    need_to_yield = self.handle_backslash()
                except:
                    #cleaning up after bad input...
                    self.buffer.clear()
                    self.res = ''
                    raise
            elif char == ';':
                #unescaped semicolons need to be treated as newlines.
                need_to_yield = True
            else:
                need_to_yield = self.handle_normal_char(char)

            if need_to_yield:
                yield self.res
                self.res = ''
