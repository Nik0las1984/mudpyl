"""Automatically sip health and mana vials."""
from mudpyl.library.autosipper import GenericAutosipper
from mudpyl.triggers import binding_trigger
import re

class AchaeanAutosipper(GenericAutosipper):
    """Keeps track of your max health, and sips health and mana for you."""

    def __init__(self, max_health, max_mana):
        GenericAutosipper.__init__(self, max_health, max_mana)
        self.prompt_seen.regex = re.compile("(\d+)h, (\d+)m, \d+e, \d+w "
                                            "c?e?x?k?d?b?-")

    def calculate_threshold(self):
        """Recaulculate the maximum sipping health and mana."""
        healthsip = (self.max_health * 0.15 + 100) * 1.2
        self.health_threshold = self.max_health - healthsip

        manasip = (self.max_mana * 0.15 + 100) * 1.2
        self.mana_threshold = self.max_mana - manasip

    @binding_trigger("^Health: \d+/(\d+) Mana: \d+/(\d+)$")
    def set_max_values(self, match, realm):
        """Record what our maximum health and mana are."""
        self.max_health, self.max_mana = match.groups()
        self.calculate_threshold()

    @property
    def triggers(self):
        #XXX: this is more than a bit clumsy
        return [self.set_max_values] + GenericAutosipper.triggers.fget(self)
