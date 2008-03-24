"""Utility for passing around lines with their colour information."""
from bisect import insort
from itertools import izip, tee, chain

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

def pairwise(seq):
    """Return a list pairwise.

    Example::
        >>> pairwise([1, 2, 3, 4])
        [(1, 2), (2, 3), (3, 4)]
    """
    a, b = tee(seq)
    try:
        b.next()
    except StopIteration:
        pass
    return izip(a, b)

class _LoopingLast(list):
    """A list whose final value is repeated infinitely."""

    def __getitem__(self, ind):
        if ind >= len(self):
            return self[-1]
        else:
            return list.__getitem__(self, ind)

class RunLengthList(object):
    """A list represented by a value and its start point.
    
    Thus, the data is using run-length coding. The data passed into this class
    must not have a 'gap' at the beginning, otherwise Bad Things may happen.
    If multiple runs start at the same index (ie, it is not normalised), other
    Bad Things (related to insort, order and consistency) may happen.
    """

    def __init__(self, values, _normalised = False):
        #pairwise works off of itertools.tee, so this isn't broken for
        #generators.
        self.values = values
        if not _normalised:
            self._normalise()
        if not self.values:
            raise ValueError("The list of values must not be empty.")
        if self.values[0][0] != 0:
            raise ValueError("All the indices must be specified - no gap!")

    def as_populated_list(self):
        """Return a normal array of values. 
        
        Each index represents what the index's value is, and the last index
        loops infinitely.
        """
        res = []
        for (start, val), (end, _) in pairwise(self.values):
            res += [val] * (end - start)
        #our very last value won't be plucked by the above loop, so we add
        #it here.
        if self.values:
            res.append(self.values[-1][1])
        return _LoopingLast(res)

    def as_pruned_index_list(self):
        """Return an unwrapped unredundant run-length list."""
        #don't want to share references of mutable data
        return self.values[:]

    def _normalise(self):
        """Remove redundancies."""
        res = []
        cur = object() #sentinel
        #we can have None here, because only the first member of the pairwise
        #(index, value) will be used, and it'll only be right at the end. In
        #fact, only the first one being used is the very reason we need to
        #do this: how else will the final value get out there?
        values = chain(self.values, [(object(), None)])
        for (start, val), (end, _) in pairwise(values):
            if start != end and cur != val:
                cur = val
                res.append((start, val))
        self.values = res

    def add_colour(self, ind, value):
        """Add a value starting at a specific point."""
        #remove any other colours present at this index. Because bisect won't
        #accept a custom compare function, it will always compare both the key
        #and the value of our tuples. But, if the value we're adding sorts
        #before the present value, this means that it will be obliterated
        #by the normalisation. Therefore, better safe than sorry.
        for num, (other_ind, _) in enumerate(self.values):
            if other_ind == ind:
                del self.values[num]
        insort(self.values, (ind, value))
        self._normalise()

    def _make_explicit(self, ind):
        """Make the implicit value at a point explicit.
        
        The value to use is given by the previous entry in the index list. The
        list is left in a non-normalised state - this method should only be
        used as an intermediate step to an end.
        """
        value = self.as_populated_list()[ind]
        insort(self.values, (ind, value))
 
    def index_adjust(self, start, change):
        """Move the values along a specific amount."""
        for num in range(len(self.values)):
            ind, col = self.values[num]
            self.values[num] = (iadjust(ind, start, change), col)
        if change < 0:
            #if the change moves things forwards, things may be made redundant
            #thus we must normalise for this case
            self._normalise()

    def blank_between(self, start, end):
        """Delete a span of values between given indexes."""
        if start == 0:
            raise ValueError("The start of the list may not be blanked.")
        #don't lose the information about what colour we end with
        self._make_explicit(end)
        res = [val for val in self.values if not start <= val[0] < end]
        self.values = res
        self._normalise()

    def delete_between(self, start, end):
        """Hardcore value removal."""
        self.index_adjust(start, start - end)

    def change_between(self, start, end, value):
        """Replace a whole span of values with a new one.
        
        This preserves the implied colour at the end.
        """
        self._make_explicit(end)
        res = [val for val in self.values if not start <= val[0] < end]
        self.values = res
        self.add_colour(start, value)

    def __eq__(self, other):
        return self.as_pruned_index_list() == other.as_pruned_index_list()

    def __repr__(self):
        return 'RunLengthList(%r)' % (self.as_pruned_index_list(),)
    __str__ = __repr__

    def copy(self):
        """Return a deep copy of ourselves."""
        return RunLengthList(self.as_pruned_index_list(), _normalised = True)

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
        self.fores.index_adjust(start, len(text))
        self.backs.index_adjust(start, len(text))
        self.line = self.line[:start] + text + self.line[start:]

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
