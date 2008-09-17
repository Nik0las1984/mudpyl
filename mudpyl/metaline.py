"""Utility for passing around lines with their colour information."""

def iadjust(ind, start, adj):
    """Moves the ind along by adj amount, unless ind is before start, when it
    is unaffected. If ind plus the adjustment would take it below start, we
    instead return start. 
    
    Careful readers will have just noted that adj may be negative, signifying 
    a move forwards. This note is for the incautious.
    """
    if start > ind:
        return ind
    if adj < 0 and (ind + adj) < start:
        return start
    return ind + adj

class _sorteddict(dict):

    def __iter__(self):
        return iter(self.keys())
    iterkeys = __iter__

    def keys(self):
        return sorted(dict.__iter__(self))

    def iteritems(self):
        return ((k, self[k]) for k in self)

    def items(self):
        return list(self.iteritems())

    def itervalues(self):
        return (self[k] for k in self)

    def values(self):
        return list(self.itervalues())

    def setitems(self, items):
        self.clear()
        self.update(items)

class RunLengthList(_sorteddict):
    """A list represented by a value and its start point.
    
    Thus, the data is using run-length coding. The data passed into this class
    must not have a 'gap' at the beginning, otherwise Bad Things may happen.
    If multiple runs start at the same index (ie, it is not normalised), other
    Bad Things (related to insort, order and consistency) may happen.
    """

    def __init__(self, values, _normalised = False):
        _sorteddict.__init__(self, values)
        if not _normalised:
            self._normalise()
        if 0 not in self:
            raise ValueError("All the indices must be specified - no gap!")

    def _normalise(self):
        """Remove redundancies."""
        prev_val = object() #sentinel
        for key, val in self.items():
            if val == prev_val:
                del self[key]
            prev_val = val

    def add_colour(self, ind, value):
        """Add a value starting at a specific point."""
        self[ind] = value
        self._normalise()

    def get_colour_at(self, ind):
        """Return the colour at a given index."""
        val = None
        for key, new_val in self.items():
            if key > ind:
                break
            val = new_val
        return val

    def _make_explicit(self, ind):
        """Make the implicit value at a point explicit.
        
        The value to use is given by the previous entry in the index list. The
        list is left in a non-normalised state - this method should only be
        used as an intermediate step to an end.
        """
        value = self.get_colour_at(ind)
        self[ind] = value
 
    def index_adjust(self, start, change):
        """Move the values along a specific amount."""
        new_items = [(iadjust(ind, start, change), val)
                     for ind, val in self.items()]
        self.setitems(new_items)
        if change < 0:
            #if the change moves things forwards, things may be made redundant
            #thus we must normalise for this case
            self._normalise()

    def blank_between(self, start, end):
        """Delete a span of values between given indexes.

        If end is None, it blanks all the way to the end."""
        if start == 0:
            raise ValueError("The start of the list may not be blanked.")
        self._clear_between(start, end)
        self._normalise()

    def delete_between(self, start, end):
        """Hardcore value removal."""
        self.index_adjust(start, start - end)

    def _clear_between(self, start, end):
        """This possibly leaves us in a non-normalised state."""
        if end is not None:
            #don't lose the ending colour information
            self._make_explicit(end)
        #could really do with slice deletion for sorteddicts :(
        res = [val for val in self.items() if not (start <= val[0] and
                                                   (val[0] < end or
                                                    end is None))]
        self.setitems(res)
        
    def change_between(self, start, end, value):
        """Replace a whole span of values with a new one.
        
        This preserves the implied colour at the end. If end is None, then
        this changes all the way to the end.
        """
        self._clear_between(start, end)
        self.add_colour(start, value)

    def insert_list_at(self, start, length, rll):
        """Insert the list of values at the given position, shifting all the
        values right of that by the length given.
        """
        self.index_adjust(start, length)
        self._make_explicit(start + length)
        self.update([(pos + start, val) for (pos, val) in rll.items()
                     if pos < length])
        self._normalise()

    def __repr__(self):
        return 'RunLengthList(%r)' % (self.items(),)
    __str__ = __repr__

    def copy(self):
        """Return a deep copy of ourselves."""
        return RunLengthList(self, _normalised = True)

class Metaline(object):
    """A line plus some metadata.
    
    'Soft line start' means that the line does not absolutely require 
    starting on a new line. 'Soft line end' means that it can tolerate
    sharing its line with something else. When the two collide, no newline
    will be added, but otherwise a newline will be inserted to split up
    the lines.

    'wrap' indicates whether the line should be wrapped before writing to 
    an output or not.
    """

    def __init__(self, line, fores, backs, soft_line_start = False,
                 line_end = 'hard', wrap = False):
        self.line = line
        self.fores = fores
        self.backs = backs
        self.soft_line_start = soft_line_start
        self.line_end = line_end
        self.wrap = wrap

    def delete(self, start, end):
        """Delete a span of text, plus its associated metadata."""
        self.fores.delete_between(start, end)
        self.backs.delete_between(start, end)
        self.line = self.line[:start] + self.line[end:]

    def insert(self, start, text):
        """Insert a span of text."""
        #use max to stop the start of the string ever being uncoloured
        self.fores.index_adjust(max(1, start), len(text))
        self.backs.index_adjust(max(1, start), len(text))
        self.line = self.line[:start] + text + self.line[start:]

    def insert_metaline(self, start, metaline):
        """Insert a metaline at a given point."""
        length = len(metaline.line)
        self.fores.insert_list_at(start, length, metaline.fores)
        self.backs.insert_list_at(start, length, metaline.backs)
        self.line = self.line[:start] + metaline.line + self.line[start:]
        #make ourselves look tidier
        self.fores.blank_between(len(self.line), None)
        self.backs.blank_between(len(self.line), None)

    def change_fore(self, start, end, colour):
        """Change the foreground of a span of text."""
        self.fores.change_between(start, end, colour)

    def change_back(self, start, end, colour):
        """Change the background of a span of text."""
        self.backs.change_between(start, end, colour)

    def copy(self):
        """Deeply copy the metaline."""
        return Metaline(self.line, self.fores.copy(), self.backs.copy(),
                        wrap = self.wrap, line_end = self.line_end,
                        soft_line_start = self.soft_line_start)

    def __eq__(self, other):
        return all([self.line == other.line, self.fores == other.fores,
                    self.backs == other.backs, self.wrap == other.wrap,
                    self.soft_line_start == other.soft_line_start,
                    self.line_end == other.line_end])

    def __repr__(self):
        return 'Metaline(%r, %r, %r, soft_line_start = %r, '\
               'line_end = %r, wrap = %r)' % \
               (self.line, self.fores, self.backs, self.soft_line_start,
                self.line_end, self.wrap)
    __str__ = __repr__

    def __add__(self, other):
        res = self.copy()
        res.insert_metaline(len(self.line), other)
        return res

    def wrapped(self, wrapper):
        """Break outself up with newlines."""
        #this function does similar stuff to what LineAlterer does...
        #there's a very slight speedup by avoiding using fill and count('\n')
        #and instead iterating over the result of wrap, but it's not a big
        #enough win at the moment to justify the obfuscation
        if not self.wrap:
            return self
        
        metaline = self.copy()
        line = wrapper.fill(self.line)
        #we start at 0, because we're guaranteed to never start on a newline.
        prev = 0
        #adjust the indices to account for the newlines
        for _ in range(line.count('\n')):
            #add one to account for the newline we just hit.
            ind = line.index('\n', prev + 1)
            metaline.insert(ind, '\n')
            prev = ind

        return metaline

def simpleml(line, fore, back):
    """Simplified wrapper for creating simple metalines."""
    return Metaline(line, RunLengthList([(0, fore)]),
                    RunLengthList([(0, back)]))
