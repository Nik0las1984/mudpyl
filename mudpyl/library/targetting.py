"""A system for highlighting a specific patch of text and setting an in-game
target.

For: Achaea.
"""
from mudpyl.triggers import binding_trigger
from mudpyl.aliases import binding_alias
from mudpyl.modules import BaseModule
from mudpyl.colours import HexFGCode
import re

#XXX: this will need to be updated when the Big Bad Combat System comes in,
#     because that will need to know about our target so we can track their
#     rebounding, herb eating, salve application, etc.

class Targetter(BaseModule):
    """Dynamically highlights a given name or piece of text."""

    def __init__(self, factory):
        super(Targetter, self).__init__(factory)
        self.target = None

    @property
    def triggers(self):
        """The triggers we need to have added."""
        return [self.target_seen]

    @property
    def aliases(self):
        """The aliases we need to have added."""
        return [self.set_target, self.clear_target]

#pylint likes complaining about the unused arguments in the callbacks, which
#are actually perfectly harmless.
#pylint: disable-msg=W0613

    @binding_alias('^k (.*)$')
    def set_target(self, match, realm):
        """Change the target."""
        self.target = match.group(1)
        #account for plural, possessive, and both blural possessives, and only
        #when it's a word on its lonesome.
        self.target_seen.regex = re.compile(r"\b%ss?'?s?\b" % self.target,
                                            re.IGNORECASE)
        realm.send_to_mud = False
        realm.send("settarget tar %s" % self.target)
    
    @binding_alias('^t(arget)?clear$')
    def clear_target(self, match, realm):
        """Clear the previously set target."""
        realm.send_to_mud = False
        self.target_seen.regex = self.target = None
        realm.send("cleartarget tar")

    @binding_trigger(None)
    def target_seen(self, match, realm):
        """We've seen the target. Highlight it."""
        realm.alterer.change_fore(match.start(), match.end(), 
                                 HexFGCode(0xFF, 0x00, 0x00))


#pylint: enable-msg=W0613
