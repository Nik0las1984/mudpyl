"""Tracks afflictions, rather naively."""
from mudpyl.modules import EarlyInitialisingModule
from mudpyl.triggers import non_binding_trigger

class AffTracker(EarlyInitialisingModule):
    """Tracks afflictions and adds them to a set of afflictions."""

    def __init__(self, affpats):
        self.afflicted_this_round = set()
        self.triggers = [self.make_aff_trigger(pat, aff, attacks)
                         for pat, aff, attacks in affpats]

    def make_aff_trigger(self, pat, aff, attacks):
        """Constructs a trigger for the given attern, affliction name and
        the attacks that can cause it.
        """
        @non_binding_trigger(pat)
        def aff_message_seen(match, realm):
            """Check that it was possible to be hit by the affliction, then
            add it to our set of afflictions.
            """
            if realm.hit_tracker.attack_type in attacks:
                self.afflicted(aff)
        return aff_message_seen()

    def afflicted(self, affliction):
        """Mark ourselves as afflicted this round."""
        self.afflicted_this_round.add(affliction)
