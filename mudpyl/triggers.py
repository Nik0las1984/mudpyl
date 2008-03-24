"""Implementes triggers, which run code if the MUD's text matches certain
criteria.
"""
from collections import deque
from mudpyl.matchers import BindingPlaceholder, NonbindingPlaceholder, \
                            make_decorator, ProtoMatcher, BaseMatchingRealm
from mudpyl.metaline import iadjust
from mudpyl.aliases import AliasMatchingRealm
import re

class RegexTrigger(ProtoMatcher):
    """A single trigger, that matches simply on a regex."""

    def match(self, metaline):
        """Test to see if the trigger's regex matches."""
        if self.regex is not None:
            return re.finditer(self.regex, metaline.line)
        else:
            return []

binding_trigger = make_decorator(RegexTrigger, BindingPlaceholder)
non_binding_trigger = make_decorator(RegexTrigger, NonbindingPlaceholder)

class LineAlterer(object):
    """Caches the changes made to a Metaline so triggers don't step on each
    others' feet.
    """

    def __init__(self):
        self._changes = deque()

    def delete(self, start, end):
        """Delete a span of text."""
        self._changes.append(('delete', start, end))

    def insert(self, start, text):
        """Insert text."""
        self._changes.append(('insert', start, text))

    def change_fore(self, start, end, colour):
        """Change a span's foreground."""
        self._changes.append(('change_fore', start, end, colour))

    def change_back(self, start, end, colour):
        """Change a span's background."""
        self._changes.append(('change_back', start, end, colour))

    def _alter(self, start, adjustment):
        """Change the indices to account for deletions and insertions."""
        res = deque()
        for change in self._changes:
            if change[0] == 'delete':
                meth, mstart, mend = change
                res.append((meth, iadjust(mstart, start, adjustment), 
                            iadjust(mend, start, adjustment)))
            elif change[0] == 'insert':
                meth, mstart, text = change
                res.append((meth, iadjust(mstart, start, adjustment), text))
            elif change[0] in ('change_fore', 'change_back'):
                meth, mstart, mend, colour = change
                res.append((meth, iadjust(mstart, start, adjustment), 
                            iadjust(mend, start, adjustment), colour))
        self._changes = res

    def apply(self, metaline):
        """Apply our changes to a metaline.

        This LineAlterer is no good after doing this, so copy it if it needs
        to be reused.
        """
        metaline = metaline.copy()
        while self._changes:
            change = self._changes.popleft()
            meth = change[0]
            args = change[1:]
            if meth == 'delete':
                start, end = args
                #we want the adjustment to be negative
                self._alter(start, start - end)
            elif meth == 'insert':
                start, text = args
                self._alter(start, len(text))
            getattr(metaline, meth)(*args)
        return metaline

class TriggerMatchingRealm(BaseMatchingRealm):
    """A realm representing the matching of triggers.
    
    This has several things that triggers can twiddle:
     
    .alterer - a LineAlterer instance that triggers must use if they want to
    fiddle with the metaline.
    
    .display_line, which indicates whether the line should be displayed on
    screen or not.
    
    There are also several attributes which should not be altered by triggers,
    but which may be read or something:
    
    .metaline, which is the Metaline that the trigger matched against.
    
    .root, which is the RootRealm.
    
    .parent, which is the Realm up one level from this one.
    """

    def __init__(self, metaline, root, parent):
        BaseMatchingRealm.__init__(self, root, parent)
        self.metaline = metaline
        self.alterer = LineAlterer()
        self.display_line = True

    def process(self):
        """Do our main thing."""
        self._match_generic(self.metaline, self.root.triggers)
        metaline = self.alterer.apply(self.metaline)
        if self.display_line:
            self.parent.write(metaline)
        for noteline, sls in self._writing_after:
            self.parent.write(noteline, sls)

    def send(self, line, echo = False):
        """Send a line to the MUD."""
        #need to spin a new realm out here to make sure that the writings from
        #the alias go after ours.
        realm = AliasMatchingRealm(line, echo, parent = self, 
                                   root = self.root)
        realm.process()
