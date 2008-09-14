"""Utilities and stuff for HTML logging."""
from cgi import escape
from mudpyl.modules import BaseModule
from mudpyl.colours import fg_code, bg_code, WHITE, BLACK
import time
import os

class HTMLLogOutput(object):
    """Handles the HTML log."""
   
    #these may be overriden in subclasses if they want to log in some other
    #way using different pre/postambles.
    log_preamble = '''
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<style>
body {
    background: black;
    font-family: monospace;
    font-size: 8pt;
}
</style>
</head>
<body>
<span style="color: #B0B0B0; background: #000000">
<pre>
'''

    log_postamble = '''
</span>
</pre>
</body>
</html>
'''

    colour_change = '''</span><span style="color: #%s; background: #%s">'''

    def __init__(self, realm, logformat):
        self.fore = fg_code(WHITE, False)
        self.back = bg_code(BLACK)
        self.realm = realm
        self._dirty = False
        realm.addProtocol(self)
        self.log = open(time.strftime(logformat) % 
                                   {'name': self.realm.factory.name}, 'a')
        self.log.write(self.log_preamble)

    def write_out_span(self, span):
        """Write a span of coloured text to the log, using our most recent
        colour setup.
        """
        self.log.write(escape(span))

    def change_colour(self):
        """The change itself is useless, as we'd have to write a new <span>
        anyway with both foreground and background, so use common code for
        both types of change.
        """
        self.log.write(self.colour_change % (self.fore.tohex(), 
                                             self.back.tohex()))
        self._dirty = False

    def close(self):
        """Clean up."""
        if self.log is not None:
            self.log.write(self.log_postamble)
            self.log.close()

    def connectionMade(self):
        """The realm sends out the 'coonection made at X' notes."""
        pass
    connectionLost = connectionMade

    def metalineReceived(self, metaline):
        """Write the line to the logs.

        This breaks the string up into coloured chunks, and feeds them to
        the log separately."""
        line = metaline.line
        #the indices are relative to the original string, not the previous
        #index, so we need to track what the previous index was to figure out
        #how much of the string needs to be coloured.
        oldind = 0

        for ind, change in sorted(metaline.fores.items() +
                                  metaline.backs.items()):
            #calculate the length of the previous bit of coloured string
            inddiff = ind - oldind
            if len(line) >= inddiff > 0:
                if self._dirty:
                    self.change_colour()
                self.write_out_span(line[:inddiff])
            if change.ground == 'back':
                self._dirty = self.back != change
                self.back = change
            elif change.ground == 'fore':
                self._dirty = self.fore != change
                self.fore = change
            else:
                raise RuntimeError("Dunno what %r is." % change)
            line = line[inddiff:]
            oldind = ind
        
        if self._dirty:
            self.change_colour()
        if line:
            self.write_out_span(line)

class HTMLLoggingModule(BaseModule):
    """A module that logs to disk."""

    #defaultly log to a file in ~/logs/
    logplace = os.path.join(os.path.expanduser('~'), 'logs',
                            '%%(name)s/Date %Y %m %d Time %H %M %S.html')

    def is_main(self):
        """Open up the HTML log."""
        #automatically adds itself to the outputs list
        HTMLLogOutput(self.realm, self.logplace)

