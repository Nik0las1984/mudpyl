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
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<style>
body {
    background: black;
    font-family: Courier New, monospace;
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

    def __init__(self, outputs, realm, logformat):
        self.outputs = outputs
        outputs.add_output(self)
        realm.add_connection_receiver(self)
        self.log = open(time.strftime(logformat) % 
                                   {'name': self.outputs.factory.name}, 'a')
        self.log.write(self.log_preamble)

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

    def connection_made(self):
        """The realm sends out the 'coonection made at X' notes."""
        pass
    connection_lost = connection_made

class HTMLLoggingModule(BaseModule):
    """A module that logs to disk."""

    #defaultly log to a file in ~/logs/
    logplace = os.path.join(os.path.expanduser('~'), 'logs',
                            '%%(name)s/Date %Y %m %d Time %H %M %S.html')

    def is_main(self):
        """Open up the HTML log."""
        #automatically adds itself to the outputs list
        HTMLLogOutput(self.realm.factory.outputs, self.realm, self.logplace)

