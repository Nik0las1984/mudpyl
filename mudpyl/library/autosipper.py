"""Automatically sips health.

For: IRE MUDs.
"""
from mudpyl.modules import EarlyInitialisingModule
from mudpyl.aliases import binding_alias
from mudpyl.triggers import binding_trigger

class GenericAutosipper(EarlyInitialisingModule):

    """Automatically sips health and tracks what its sip threshold should be.
    """

    def __init__(self, max_health, max_mana):
        self.max_health = max_health
        self.max_mana = max_mana
        self.health_threshold = 0
        self.mana_threshold = 0
        self.state = 'sip balance'
        self.calculate_threshold()

#pylint likes complaining about the unused arguments in the callbacks, which
#are actually perfectly harmless.
#pylint: disable-msg=W0613

    @binding_trigger(None)
    def prompt_seen(self, match, realm):
        """We've seen a prompt. Do we need to sip?"""
        health, mana = match.groups()
        health = int(health)
        mana = int(mana)
        #TODO: account for anorexia, pausing, etc

        if self.state == 'sip balance':
            if health <= self.health_threshold:
                realm.send('drh')
            elif mana <= self.mana_threshold:
                realm.send('drm')

    @binding_alias('^drh$')
    def sip_health(self, match, realm):
        """Sip from our health vial."""
        self.state = 'off balance'
        realm.send('drink health')
        realm.send_to_mud = False

    @binding_alias("^drm$")
    def sip_mana(self, match, realm):
        """Sip from our mana vial."""
        self.state = 'off balance'
        realm.send("drink mana")
        realm.send_to_mud = False

    @binding_trigger('^You may drink another healing elixir\.$')
    def got_balance(self, match, realm):
        """We've gotten sip balance back."""
        if self.state == 'off balance':
            self.state = 'sip balance'
#pylint: enable-msg=W0613

    @property
    def triggers(self):
        """The triggers we want added."""
        return [self.prompt_seen, self.got_balance]

    @property
    def aliases(self):
        """The aliases we want added."""
        return [self.sip_health, self.sip_mana]

    def calculate_threshold(self):
        """Work out what our sipping thresholds are."""
        raise NotImplementedError
