"""Common code to both triggers and aliases.

This includes a base class, and utilities for constructing them, especially
using decorators around functions.
"""
import re
import traceback

class ProtoMatcher(object):
    """Common code to triggers and aliases.

    self.func must be a function that accepts two arguments: a MatchObj (or
    whatever the overriden .match() returns), and a TriggerInfo. The
    TriggerInfo is a structure containing other useful things, as well as some
    flags the triggers can set to change the behaviour of the client.
    """

    def __init__(self, regex = None, func = None, sequence = 0):
        if func is not None or not hasattr(self, 'func'):
            self.func = func
        if regex is not None or not hasattr(self, 'regex'):
            self.regex = regex
        self.sequence = sequence

#pylint doesn't like that func is set in __init__ too, if the conditions are
#right. Also, the unused arguments are harmless.
#pylint: disable-msg=E0202,W0613
    def func(self, match, realm):
        """Default, do-nothing function."""
        pass
#pylint: enable-msg=E0202,W0613

    def __call__(self, match, realm):
        realm.trace_thunk(lambda: "%s matched!" % self)
        try:
            self.func(match, realm)
        except Exception: #don't catch KeyboardInterrupt etc
            traceback.print_exc()

    def __cmp__(self, other):
        return cmp(self.sequence, other.sequence)

    def __str__(self):
        args = [type(self).__name__]
        #make it do the right thing for both strings and compiled patterns.
        if isinstance(self.regex, basestring):
            args.append(repr(self.regex))
        elif self.regex is not None:
            args.append(repr(self.regex.pattern))
        else:
            args.append('(inactive)')
        #scrape our function's name, if it's interesting
        if self.func is not None and self.func.func_name != 'func':
            args.append(self.func.func_name)
        args.append('sequence = %d' % self.sequence)
        return '<%s>' % ' '.join(args)

class _Placeholder(object):
    """Represents a matcher that's actually initialised later."""

    def cls(self, regex, func, sequence):
        raise NotImplemented

    def __init__(self, regex, func, sequence):
        self.regex = regex
        self.func = func
        self.sequence = sequence

class BindingPlaceholder(_Placeholder):
    """A holding stage for triggers/aliases on the class, which each instance
    binds to themselves.

    Kind of like bound methods, really.
    """

    def __init__(self, *args):
        _Placeholder.__init__(self, *args)
        #TODO: should be a WeakKeyDictionary. When I get around to it.
        self._catered_for = {}

    def __get__(self, instance, owner):
        #return our unbound version (ie, self)   
        if instance is None:
            return self
        #check to see if we've already bound ourselves to this instance or not
        if id(instance) not in self._catered_for:
            #pylint doesn't know we dynamically mess with self.cls in child
            #classes
            #pylint: disable-msg= E1111
            res = self.cls(self.regex, self.func.__get__(instance, owner), 
                           self.sequence)
            #pylint: enable-msg= E1111
            self._catered_for[id(instance)] = res
            return res
        else:
            return self._catered_for[id(instance)]

class NonbindingPlaceholder(_Placeholder):
    """Wraps up functions as standalone matchers."""

    def __call__(self):
        return self.cls(self.regex, self.func, self.sequence)

def make_decorator(class_, base):
    """Creates a decorator that does many varied and useful things."""
    class _PlaceholderClass(base):
        #dynamic inheritance and class creation, woo
        cls = class_

    def instance_class(regex, sequence = 0):
        """The actual decorator."""
        if isinstance(regex, basestring):
            regex = re.compile(regex)
        def fngrabber(func):
            return _PlaceholderClass(regex, func, sequence)
        return fngrabber

    return instance_class

class BaseMatchingRealm(object):

    """A realm representing the matching of triggers or aliases."""

    def __init__(self, root, parent, send_line_to_mud):
        self.root = root
        self.parent = parent
        self._writing_after = []
        self.send_line_to_mud = send_line_to_mud

    def _write_after(self):
        """Write everything we've been waiting to."""
        for noteline, sls in self._writing_after:
            self.parent.write(noteline, sls)

    def write(self, line, soft_line_start = False):
        """Write a line to the screen.

        This buffers until the original line has been displayed or echoed.
        """
        self._writing_after.append((line, soft_line_start))

    def send(self, line, echo = False):
        """Send a line to the MUD immediately."""
        self.parent.send(line, echo)

    def _match_generic(self, line, matchers):
        """Test each matcher against the given line, and run the functions
        of those that match.

        This is suitable for use with either triggers or aliases, because of
        the commonality of their APIs.
        """
        for matcher in matchers:
            matches = matcher.match(line)
            for match in matches:
                matcher(match, self)

    def trace(self, line):
        """Forward the debugging decision to our parent."""
        self.parent._trace_with(line, self)

    def trace_thunk(self, thunk):
        self.parent._trace_thunk_with(thunk, self)

    def _trace_with(self, line, realm):
        """Forward a trace request up the stack of realms."""
        self.parent._trace_with(line, realm)

    def _trace_thunk_with(self, thunk, realm):
        self.parent._trace_thunk_with(thunk, realm)
