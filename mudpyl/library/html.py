"""Utilities and stuff for HTML logging."""
from cgi import escape
from mudpyl.modules import BaseModule
import time
import os

class HTMLLogOutput(object):
    """Handles the HTML log."""
   
    #these may be overriden in subclasses if they want to log in some other
    #way using different pre/postambles.
    log_preamble = '''
<html>
<head>
<style>
body {
    background: black;
    font-family: Courier New, monospace;
    font-size: 8pt;
}
</style>
</head>
<body>
<pre>
'''

    log_postamble = '''
</span>
</pre>
</body>
</html>
'''

    colour_change = '''</span><span style="color: #%s; background: #%s">'''

    connection_closed_message = '''</span><span style="color: #FFAA00
background: #000000">
Connection closed at %H:%M:%S'''

    connection_opened_message = '''<span style="color: #FFAA00">
Connection opened at %H:%M:%S</span>
<span style="color: #B0B0B0; background: #000000">
'''

    def __init__(self, outputs, logformat):
        self.outputs = outputs
        outputs.add_output(self)
        self.log = open(time.strftime(logformat) % 
                                   {'name': self.outputs.factory.name}, 'a')
        self.log.write(self.log_preamble)

    def peek_line(self, line):
        """We don't need to peek at the line."""
        pass

    def write_out_span(self, span):
        """Write a span of coloured text to the log, using our most recent
        colour setup.
        """
        self.log.write(escape(span))

    def colour_changed(self, _):
        """The change itself is useless, as we'd have to write a new <span>
        anyway with both foreground and background, so use common code for
        both types of change.
        """
        self.log.write(self.colour_change % (self.outputs.fore.tohex(), 
                                             self.outputs.back.tohex()))

    fg_changed = bg_changed = colour_changed

    def close(self):
        """Clean up."""
        if self.log is not None:
            self.log.write(self.log_postamble)
            self.log.close()

    def connection_opened(self):
        """Write a note to the log about when the connection opened."""
        self.log.write(time.strftime(self.connection_opened_message))

    def connection_closed(self):
        """Write a note to the log about when the connection closed."""
        self.log.write(time.strftime(self.connection_closed_message))

class HTMLLoggingModule(BaseModule):
    """A module that logs to disk."""

    #defaultly log to a file in ~/logs/
    logplace = os.path.join(os.path.expanduser('~'), 'logs',
                            '%%(name)s/Date %Y %m %d Time %H %M %S.html')

    def is_main(self):
        """Open up the HTML log."""
        #automatically adds itself to the outputs list
        HTMLLogOutput(self.realm.factory.outputs, self.logplace)

