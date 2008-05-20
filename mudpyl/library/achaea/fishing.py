"""Deepsea fishing system for Achaea."""
from mudpyl.triggers import binding_trigger
from mudpyl.aliases import binding_alias
from mudpyl.modules import BaseModule

def send_later(realm, delay, line):
    """Do something after a given delay."""
    #needs a late import, otherwise the GUI won't be allowed to pick the right
    #reactor. This could be fixed by spliitting the configure function into
    #the bits that don't need the factory, and the bits that do. But that
    #seems like overcomplication when one local import fixes this.
    from twisted.internet import reactor
    #also, pylint fails at twisted's magic
    #pylint: disable-msg=E1101
    reactor.callLater(delay, realm.send, line)
    #pylint: enable-msg=E1101

class FishingSystem(BaseModule):
    """Module for deepsea fishing."""

    def __init__(self, realm):
        BaseModule.__init__(self, realm)
        self.stopped_reeling = False

    #make pylint give the 'unused argument' stuff a rest
    #pylint: disable-msg=W0613
    @binding_trigger("Relaxing the tension on your line, you are able to "
                     "reel again\.")
    def reel_trigger(self, match, realm):
        """Re-reel our line to catch that fish."""
        if not self.stopped_reeling:
            realm.send("reel line")

    @binding_alias("^bc$")
    def cast_alias(self, match, realm):
        """Send out our fishing line."""
        realm.send("get carp from pole")
        realm.send("get carp from tank")
        realm.send("bait hook with carp")
        #wait for balance
        send_later(realm, 5, "cast line short")
        realm.send_to_mud = False

    @binding_trigger("You (?:(?:see the water ripple as a fish makes a "
                     "medium|feel a fish make a small) strike at your "
                     "bait|stagger as a fish)")
    def jerk_trigger(self, match, realm):
        """A fish's made a strike. Wait, then jerk the line."""
        send_later(realm, 1.55, "jerk line")

    @binding_trigger("You feel a fish nibbling on your hook\.")
    def tease_trigger(self, match, realm):
        """Tease to try and get a bite."""
        send_later(realm, 2.1, "tease line")

    @binding_trigger("You quickly jerk back your fishing pole and feel "
                     "the line go taut. You've hooked")
    def start_reeling_trigger(self, match, realm):
        """Okay, let's start reelin once we get balance."""
        send_later(realm, 3, "reel line")
        self.stopped_reeling = False

    @binding_trigger("You (?:quickly reel in a |reel in the last bit of "
                     "line and your struggle is over)|With a final tug, you "
                     "finish reeling|As the fish strains your line beyond its "
                     "breaking point, it snaps suddenly,")
    def recast_trigger(self, match, realm):
        """Reeling over, let's recast."""
        realm.send("bc")
        self.stopped_reeling = True

    @property
    def triggers(self):
        """The triggers we want added."""
        return [self.reel_trigger, self.recast_trigger, self.jerk_trigger,
                self.tease_trigger, self.start_reeling_trigger]

    @property
    def aliases(self):
        """The aliases we want added."""
        return [self.cast_alias]
