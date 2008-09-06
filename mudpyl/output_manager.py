"""Orchestrates and coordinates the writing of output (eg, to screen and 
to logs).
"""
from mudpyl.colours import WHITE, BLACK, fg_code, bg_code

class OutputManager(object):
    """Handles:
         - colour tracking
         - line wrapping
         - some other stuff I've forgotten.
    """

    def __init__(self, factory):
        self.factory = factory
        self.outputs = []
        #sensible defaults
        self.fore = fg_code(WHITE, False)
        self.back = bg_code(BLACK)
        factory.realm.addProtocol(self)

    def add_output(self, output):
        """Add another output that wants to receive stuff."""
        self.outputs.append(output)
        
    def metalineReceived(self, metaline):
        """Write the line to the logs and screen."""
        allcolours = sorted(metaline.fores.values + metaline.backs.values)
        self._actually_write_to_screen(allcolours, metaline.line)

    def _actually_write_to_screen(self, allcolours, line):
        """Actually break the string up into coloured chunks, and feed these
        to the outputs.
        """
        #the indices are relative to the original string, not the previous
        #index, so we need to track what the previous index was to figure out
        #how much of the string needs to be coloured.
        oldind = 0

        for ind, change in allcolours:
            #calculate the length of the coloured string
            inddiff = ind - oldind
            if inddiff > 0:
                self._write_out_span(line[:inddiff])
            self._change_colour(change)
            line = line[inddiff:]
            oldind = ind
            if not line:
                break
        
        if line:
            self._write_out_span(line)

    def _write_out_span(self, span):
        """Send a span to the outputs. Its colour is self.fore and self.back.
        """
        for output in self.outputs:
            output.write_out_span(span)

    def _change_colour(self, change):
        """Change the colour that new text will be written as.
        """
        if change.ground == 'back':
            self.back = change
            for output in self.outputs:
                output.bg_changed(change)
        elif change.ground == 'fore':
            self.fore = change
            for output in self.outputs:
                output.fg_changed(change)
        else:
            raise RuntimeError("Dunno what %r is." % change)

    def connectionMade(self):
        for output in self.outputs:
            output.connectionMade()

    def connectionLost(self):
        for output in self.outputs:
            output.connectionLost()

    def close(self):
        for output in self.outputs:
            output.close()


