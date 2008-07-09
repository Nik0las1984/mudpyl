from mudpyl.library.autosipper import GenericAutosipper
from mudpyl.triggers import binding_trigger
import re

class Autosipper(GenericAutosipper):

    def __init__(self, max_health, max_mana):
        GenericAutosipper.__init__(self, max_health, max_mana)
        self.prompt_seen.regex = re.compile("^H:(\d+) M:(\d+) E:\d+ W:\d+ "
                                            "<.*>")

    def calculate_threshold(self):
        """Calculate the threshold where we should start sipping at."""
        healthsip = (self.max_health * 11 * 0.15 + 100) / 11
        self.health_threshold = self.max_health - healthsip

        manasip = (self.max_mana * 11 * 0.15 + 100) / 11
        self.mana_threshold = self.max_mana - manasip

    @binding_trigger("^ Mana     : \d+/(\d+)\s*Reserves : \d+/\d+$")
    def mana_update(self, match, realm):
        """Recalcuate our sipping threshold based on SCORE."""
        self.max_mana = int(match.group(1))
        self.calculate_threshold()

    @binding_trigger("^ Health   : \d+/(\d+)\s*Reserves : \d+/\d+$")
    def health_update(self, match, realm):
        """Recalcuate our sipping threshold based on SCORE."""
        self.max_health = int(match.group(1))
        self.calculate_threshold()

    @property
    def triggers(self):
        #XXX: clumsy
        return [self.mana_update, self.health_update] + \
               GenericAutosipper.triggers.fget(self)
