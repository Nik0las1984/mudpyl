"""Tracks afflictions, rather naively."""
from mudpyl.modules import EarlyInitialisingModule
from mudpyl.triggers import non_binding_trigger

class Curer(EarlyInitialisingModule):
    """Tracks afflictions and adds them to a set of afflictions."""

    def __init__(self, afflictions_file = 'afflictions.csv',
                 attack_messages_file = 'attack_messages.csv',
                 attacks_file = 'attacks.csv',
                 affliction_classes_file = 'aff_classes.csv'):
        self.illusioned = False
        self.afflictions = set()
        self.afflicted_this_round = set()
        self.attacks_this_round = []
        self.aff_classes = dict((aff_class, frozenset(attacks))
                                for aff_class, attacks
                                in self.load_csv(affliction_classes_file))
        self.attacks = dict((attack, (frozenset(prereq), damages == 'true',
                                      follows_attacks))
                             for attack, prereq, damages, follows_attacks
                             in self.load_csv(attacks_file))
        self.triggers = []
        self.triggers += [self.make_aff_trigger(pat, aff, aff_classes, prereq)
                          for pat, aff, aff_classes, prereq
                          in self.load_csv(afflictions_file)]
        self.triggers += [self.make_hit_trigger(pat, attack) for pat, attack
                          in self.load_csv(attack_messages_file)]

    def load_csv(self, name):
        raise NotImplementedError

    def make_aff_trigger(self, pat, aff, aff_classes, prereq):
        """Constructs a trigger for the given attern, affliction name and
        the attacks that can cause it.
        """
        prereq = frozenset(prereq)
        #we need to come before the hit triggers
        @non_binding_trigger(pat, sequence = -1)
        def aff_message_seen(match, realm):
            """Check that it was possible to be hit by the affliction, then
            add it to our set of afflictions.
            """
            self.afflicted(aff)
            if not (self.check_aff_class(aff_classes) and
                    self.afflictions >= prereq):
                self.illusioned = True
        return aff_message_seen()

    def make_hit_trigger(self, pat, attack):
        prereq_affs, does_damage, attacks_can_precede = self.attacks[attack]
        @non_binding_trigger(pat)
        def hit_message_seen(match, realm):
            """Check that we should have just seen that attack message, then
            record it as a hit.
            """
            if not (prereq_affs <= self.afflictions and
                    self.attack_type in attacks_can_precede):
                self.illusioned = True
            self.hit(attack)
        return hit_message_seen()

    def check_aff_class(self, aff_classes):
        """Should we have just seen that affliction class following that
        attack?
        """
        return any(self.attack_type in self.aff_classes[aff_class]
                   for aff_class in aff_classes)

    def afflicted(self, affliction):
        """Mark ourselves as afflicted this round."""
        if affliction not in self.afflictions:
            self.afflicted_this_round.add(affliction)
            self.afflictions.add(affliction)

    def hit(self, attack_type):
        """Set our previous attack type."""
        self.attacks_this_round.append(attack_type)

    @property
    def attack_type(self):
        """Return the type of the last attack, or None if there were none
        yet this round."""
        if not self.attacks_this_round:
            return 'none'
        else:
            return self.attacks_this_round[-1]
