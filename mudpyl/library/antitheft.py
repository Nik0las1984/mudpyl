"""Keeps your stuff for you.

For: Achaea.
"""
from mudpyl.aliases import binding_alias
from mudpyl.triggers import binding_trigger
from mudpyl.modules import EarlyInitialisingModule
import re

class AntitheftSystem(EarlyInitialisingModule):
    """A system to stop your things getting taken."""

    def __init__(self, protected, armour):
        self.protected = [(re.compile(pat), items) 
                          for pat, items in protected]
        self.allowing_gold_get = False
        self.allowing_remove = False
        self.armour_removed = False
        self.armour = armour

    @property
    def triggers(self):
        """The triggers we need added."""
        return [self.gold_gotten,
                self.removed,
                self.balance]

    @property
    def aliases(self):
        """The aliases we need added."""
        return [self.get_gold,
                self.remove]

#pylint likes complaining about the unused arguments in the callbacks, which
#are actually perfectly harmless.
#pylint: disable-msg=W0613

    @binding_trigger("^You get \d+ gold sovereigns? from (.*)\.$")
    def gold_gotten(self, match, realm):
        """We've taken some gold out.

        Check if this is allowed, and if it's not, try and put it back.
        """
        if self.allowing_gold_get:
            self.allowing_gold_get = False
            return
        for pat, items in self.protected:
            if pat.match(match.group(1)):
                for item in items:
                    realm.send("#repeat 3 put money in %s" % item)

    @binding_trigger("^You (?:drop|remove) (.*)\.$")
    def removed(self, match, realm):
        """Check to see if we're allowed to remove the object, and if not,
        try and rewear it.
        """
        if self.allowing_remove:
            self.allowing_remove = False
            return
        for pat, items in self.protected:
            if pat.match(match.group(1)):
                for item in items:
                    if item == self.armour:
                        self.armour_removed = True
                    realm.send("#repeat 3 get %s" % item)
                    realm.send("#repeat 3 wear %s" % item)

    @binding_trigger("^You have recovered balance on all limbs\.$")
    def balance(self, match, realm):
        """If we've previously taken off our armour, try and put it back on
        now.
        """
        if self.armour_removed:
            self.armour_removed = False
            realm.send("#repeat 3 get %s" % self.armour)
            realm.send("#repeat 3 wear %s" % self.armour)

    @binding_alias('^get (\d+) gold from (.*)$')
    def get_gold(self, match, realm):
        """Allow ourselves to get the gold out."""
        if not self.allowing_gold_get:
            self.allowing_gold_get = True

    @binding_alias('^(remove|drop) (.*)$')
    def remove(self, match, realm):
        """Allow ourselves to remove or drop a protected item."""
        if not self.allowing_remove:
            self.allowing_remove = True

#pylint: enable-msg=W0613
