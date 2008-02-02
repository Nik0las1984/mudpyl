"""Automatically sips health.

For: Imperian.
"""
from mudpyl.modules import EarlyInitialisingModule
from mudpyl.aliases import binding_alias
from mudpyl.triggers import binding_trigger

class Autosipper(EarlyInitialisingModule):

    """Automatically sips health and tracks what its sip threshold should be.
    """

    def __init__(self, max_health, max_mana):
        self.max_health = max_health
        self.health_threshold = 0
        self.state = 'sip balance'
        self.calculate_threshold()
        #TODO: expand to do mana as well

    @binding_trigger('^H:(\d+) M:(\d+) E:\d+ W:\d+ <.*>')
    def prompt_seen(self, match, realm):
        """We've seen a prompt. Do we need to sip?"""
        health, mana = match.groups()
        health = int(health)
        mana = int(mana)

        if self.state == 'sip balance':
            if health <= self.health_threshold:
                realm.send('drh')
            #TODO: mana here too

    @binding_alias('^drh$')
    def sip_health(self, match, realm):
        """Sip from our health vial."""
        #TODO: don't be so trusting. Add a timeout and a trigger for when we
        #actually sip
        self.state = 'off balance'
        realm.send('drink health')
        realm.send_to_mud = False

    @binding_trigger('^You may drink another healing elixir\.$')
    def got_balance(self, match, realm):
        """We've gotten sip balance back."""
        if self.state == 'off balance':
            self.state = 'sip balance'

    @binding_trigger('^ Health   : \d+/(\d+)\s*Reserves : \d+/\d+$')
    def health_update(self, match, realm):
        """Recalcuate our sipping threshold based on SCORE."""
        self.max_health = int(match.group(1))
        self.calculate_threshold()

    @property
    def triggers(self):
        """The triggers we want added."""
        return [self.prompt_seen, self.got_balance, self.health_update]

    @property
    def aliases(self):
        """The aliases we want added."""
        return [self.sip_health]

    def calculate_threshold(self):
        """Calculate the threshold where we should start sipping at."""
        sip = (self.max_health * 11 * 0.15 + 100) / 11
        self.health_threshold = self.max_health - sip
