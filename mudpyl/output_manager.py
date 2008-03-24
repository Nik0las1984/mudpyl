"""Orchestrates and coordinates the writing of output (eg, to screen and 
to logs).
"""
from textwrap import TextWrapper
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
        self.metaline_peekers = []
        self.last_line_end = None
        #sensible defaults
        self.fore = fg_code(WHITE, False)
        self.back = bg_code(BLACK)
        self.wrapper = TextWrapper(width = 100, 
                                  drop_whitespace = False)

    def add_output(self, output):
        """Add another output that wants to receive stuff."""
        self.outputs.append(output)

    def add_metaline_peeker(self, peeker):
        """Add an object that wants the line-wrapped metalines."""
        self.metaline_peekers.append(peeker)

    def _wrap_line(self, metaline):
        """Break an incoming line into sensible lengths."""
        #this needs to be before the futzing with NLs and GA, because textwrap
        #obliterates all other newlines.
        line = self.wrapper.fill(metaline.line)
        #we start at 0, because we're guaranteed to never start on a newline.
        prev = 0
        #adjust the indices to account for the newlines
        for _ in range(line.count('\n')):
            #add one to account for the newline we just hit.
            ind = line.index('\n', prev + 1)
            metaline.insert(ind, '\n')
            prev = ind

        return metaline
        
    def write_to_screen(self, metaline):
        """Write the line to the logs and screen."""
        if metaline.wrap:
            metaline = self._wrap_line(metaline)

        #we don't actually append newlines at the end, but the start. This
        #simplifies things, because we don't use a newline where a soft line
        #end meets a soft line start, so there's only one place in this code
        #that can add newlines.
        if self.last_line_end is not None:
            if self.last_line_end == 'hard' or not metaline.soft_line_start:
                metaline.insert(0, '\n')

        for peeker in self.metaline_peekers:
            peeker.peek_metaline(metaline)

        allcolours = sorted(metaline.fores.as_pruned_index_list() + 
                            metaline.backs.as_pruned_index_list())

        self._actually_write_to_screen(allcolours, metaline.line)

        self.last_line_end = metaline.line_end

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


