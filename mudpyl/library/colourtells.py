"""Colour-code your tell conversations by person.

For: Achaea.
"""
from collections import deque
from mudpyl.triggers import binding_trigger
from mudpyl.aliases import binding_alias
from mudpyl.colours import NORMAL_CODES, BLACK, YELLOW, fg_code
from mudpyl.modules import BaseModule

#exclude unbold black and bold yellow: the first is unreadable and the second
#is the default tell colour. We want VIBRANCY.
all_colours = set(fg_code(col, True) for col in NORMAL_CODES 
                                     if col != YELLOW) | \
              set(fg_code(col, False) for col in NORMAL_CODES 
                                      if col != BLACK)

class TellColourer(BaseModule):
    """Keeps track of who you're talking to, and colour-codes tells to and 
    from them.
    """

    def __init__(self, factory):
        BaseModule.__init__(self, factory)
        #could use an OrderedDict here instead of these two.
        self.assigned_colours = {}
        self.assigned_order = []
        self.sending_to = deque()

    def touch_name(self, name):
        """Return the colour to display name in.

        This also moves name to the end of assigned_order, which means it has
        a while until it's forcibly freed.
        """
        if name in self.assigned_order:
            #put ourselves at the end of the list for removal
            self.assigned_order.remove(name)
            self.assigned_order.append(name)
        else:
            #remove the very oldest colours until we get a free spot
            while len(self.assigned_order) >= len(all_colours):
                oldest = self.assigned_order.pop(0)
                del self.assigned_colours[oldest]

            free_colours = all_colours - set(self.assigned_colours.values())
            colour = free_colours.pop()
            self.assigned_order.append(name)
            self.assigned_colours[name] = colour

        return self.assigned_colours[name]

#pylint likes complaining about the unused arguments in the callbacks, which
#are actually perfectly harmless.
#pylint: disable-msg=W0613

    @binding_alias('(?i)^tell (\w+) .*$')
    def sending_tell(self, match, realm):
        """We're trying to send a tell. Stow away the name for safekeeping.
        """
        name = match.group(1).lower()
        self.sending_to.append(name)

    #use a non-greedy matcher for the name and title, because if we lose a bit
    #of the title's colouring, no biggie, but if we colour some of the message
    #then it's a biggie
    @binding_trigger('^You tell (.+?)( in (.*))?, ".*"$')
    def tell_sent(self, match, realm):
        """We've sent a tell. Look up who we meant it for, and colour
        appropriately.
        """
        name = self.sending_to.popleft()
        namestart = match.start(1)
        nameend = match.end(1)
        colour = self.touch_name(name)
        realm.alterer.change_fore(namestart, nameend, colour)

    @binding_trigger("^Whom do you wish to tell to\?$")
    def no_tell_sent(self, match, realm):
        """We failed to send a tell for some reason."""
        self.sending_to.popleft()

    @binding_trigger('^(\w+) tells you( in .*)?, ".*"$')
    def tell_received(self, match, realm):
        """We received a tell. Scrape out the name and colour it."""
        name = match.group(1).lower()
        nameend = match.end(1)
        colour = self.touch_name(name)
        realm.alterer.change_fore(0, nameend, colour)

#pylint: enable-msg=W0613

    @property
    def triggers(self):
        """Return the triggers we want added."""
        return [self.tell_sent, self.no_tell_sent, self.tell_received]

    @property
    def aliases(self):
        """Return the aliases we want added."""
        return [self.sending_tell]
