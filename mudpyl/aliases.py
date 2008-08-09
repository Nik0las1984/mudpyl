"""Implements aliases, which run code when the user's input matches against a
certain pattern.
"""
from mudpyl.matchers import BindingPlaceholder, NonbindingPlaceholder, \
                            ProtoMatcher, make_decorator, BaseMatchingRealm
import re

class Alias(ProtoMatcher):
    """Matches on the user's input."""

    def match(self, line):
        """Check to see if the line matches against our criteria."""
        return list(re.finditer(self.regex, line))

binding_alias = make_decorator(Alias, BindingPlaceholder)
non_binding_alias = make_decorator(Alias, NonbindingPlaceholder)

class AliasMatchingRealm(BaseMatchingRealm):
    """Represents the context that an Alias is matched in.

    This has several flags and assorted pieces of information that aliases
    can fiddle with:

    .echo is whether this line will be echoed to screen or not. The client
    will only echo lines to screen that are also being sent; if it is not
    being sent, it will not be echoed.

    .send_to_mud is whether the input line should be sent to the MUD after it
    has been through all the aliases. The default is True.

    These attributes are not settable by aliases:

    .line is the input line that is being matched against.

    .root is the Realm in charge.

    .parent is who we report to
    """

    def __init__(self, line, echo, root, parent, send_line_to_mud):
        BaseMatchingRealm.__init__(self, root, parent, send_line_to_mud)
        self.line = line
        self._sending_after = []
        self.send_to_mud = True
        self.echo = echo

    def send_after(self, line, echo = False):
        """Send a line after the current one's processing has finished."""
        self._sending_after.append((line, echo))

    def process(self):
        """Do our main thing."""
        #this looks like it's broken for correctly ordering echoing and send-
        #to-mud-ing, but it's not. The key thing to remember is that alias
        #matching -doesn't- nest like trigger matching, so the parent for any
        #AliasMatchingRealms created by an alias will be the same as ours.
        #Voila, magic.
        self._match_generic(self.line, self.root.aliases)

        if self.send_to_mud:
            if self.echo:
                self.parent.write(self.line, soft_line_start = True)
            self.send_line_to_mud(self.line)

        self._write_after()

        for sendline, echo in self._sending_after:
            self.parent.send(sendline, echo)
