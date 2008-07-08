"""Tracks what kind of attack you've been hit by."""
from mudpyl.modules import EarlyInitialisingModule
from mudpyl.triggers import non_binding_trigger

class HitTracker(EarlyInitialisingModule):
    """Tracks the previous attack that you've been hit by."""

    def __init__(self, attacks):
        self.illusioned = False
        self.attacks_this_round = []
        self.triggers = [self.make_trigger(pat, attack_type, set(affs))
                         for pat, attack_type, affs in attacks]

    def make_trigger(self, pattern, attack_type, required_affs):
        """Make a trigger for one pattern."""
        @non_binding_trigger(pattern)
        def seen_hit(match, realm):
            """Test to see if it was possible to be hit by it."""
            self.illusioned = realm.root.aff_tracker.afflictions < \
                                                               required_affs
            self.hit(attack_type)
        return seen_hit()

    def hit(self, attack_type):
        """Set our previous attack type."""
        self.attacks_this_round.append(attack_type)

    @property
    def attack_type(self):
        """Return the type of the last attack, or None if there were none
        yet this round."""
        if not self.attacks_this_round:
            return None
        else:
            return self.attacks_this_round[-1]

    def __call__(self, realm):
        realm.hit_tracker = self
        EarlyInitialisingModule.__call__(self, realm)
