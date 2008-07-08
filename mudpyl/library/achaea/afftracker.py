"""Tracks afflictions, rather naively."""
from mudpyl.modules import EarlyInitialisingModule
from mudpyl.triggers import non_binding_trigger

class AffTracker(EarlyInitialisingModule):
    """Tracks afflictions and adds them to a set of afflictions."""

    def __init__(self, affpats):
        self.illusioned = False
        self.afflictions = set()
        self.afflicted_this_round = set()
        self.triggers = [self.make_aff_trigger(pat, aff, attacks, set(prereq))
                         for pat, aff, attacks, prereq in affpats]

    def make_aff_trigger(self, pat, aff, attacks, prereq):
        """Constructs a trigger for the given attern, affliction name and
        the attacks that can cause it.
        """
        @non_binding_trigger(pat)
        def aff_message_seen(match, realm):
            """Check that it was possible to be hit by the affliction, then
            add it to our set of afflictions.
            """
            if realm.root.hit_tracker.attack_type in attacks:
                self.afflicted(aff)
                self.illusioned = not self.afflictions >= prereq
        return aff_message_seen()

    def afflicted(self, affliction):
        """Mark ourselves as afflicted this round."""
        if affliction not in self.afflictions:
            self.afflicted_this_round.add(affliction)
            self.afflictions.add(affliction)

    def __call__(self, realm):
        realm.aff_tracker = self
        EarlyInitialisingModule.__call__(self, realm)
