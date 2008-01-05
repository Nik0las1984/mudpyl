"""Harvests herbs, for Achaea."""
from mudpyl.aliases import binding_alias
from mudpyl.triggers import binding_trigger
from mudpyl.modules import BaseModule

herb_short_names = {'myrrh bush': 'myrrh', 
                    'ginseng': 'ginseng', 
                    'wild ginger': 'ginger',
                    'echinacea': 'echinacea',
                    'red elm': 'elm',
                    'lobelia': 'lobelia',
                    'bellwort': 'bellwort',
                    'black cohosh': 'cohosh',
                    'prickly ash tree': 'ash',
                    'bloodroot': 'bloodroot',
                    'irid moss': 'moss',
                    'kuzu vine': 'kuzu',
                    'kola tree': 'kola',
                    'skullcap': 'skullcap',
                    'valerian': 'valerian',
                    'goldenseal': 'goldenseal',
                    "lady's slipper": 'slipper',
                    'bayberry tree': 'bayberry',
                    'hawthorn': 'hawthorn',
                    'cactus weed': 'weed',
                    'cactus': 'pear',
                    'kelp': 'kelp',
                    'sileris': 'sileris'}

class Harvester(BaseModule):

    """Automatically goes out and harvests you herbs."""

    def __init__(self, factory):
        super(Harvester, self).__init__(factory)
        self.harvesting = False
        self.herbs_in_room = set()
        self.seen_herbs = False

    @property
    def triggers(self):
        """The triggers we need to have added."""
        return [self.balance,
                self.prompt,
                self.herb_line]

    @property
    def aliases(self):
        """The alias we need to have added."""
        return [self.harvest]

#pylint likes complaining about the unused arguments in the callbacks, which
#are actually perfectly harmless.
#pylint: disable-msg=W0613

    @binding_trigger('.*\((ginseng|myrrh bush|echinacea|red elm|lobelia|'
                      'wild ginger|bellwort|black cohosh|prickly ash tree|'
                      'bloodroot|irid moss|kuzu vine|kola tree|skullcap|'
                      "valerian|goldenseal|lady's slipper|bayberry tree|"
                      'hawthorn|cactus weed|cactus|kelp|sileris)\)\s+'
                      '(\d{1,2}) left')
    def herb_line(self, match, realm):
        """A single line from PLANTS. Add the herb to our seen herbs, if we
        can harvest it safely.
        """
        if self.harvesting:
            if int(match.group(2)) > 10:
                self.herbs_in_room.add(herb_short_names[match.group(1)])
        self.seen_herbs = True

    @binding_trigger("^You have recovered balance on all limbs\.$")
    def balance(self, match, realm):
        """We can harvest again! Check PLANTS."""
        if self.harvesting:
            realm.send("plants")

    @binding_trigger(r'^(\d+)h, (\d+)m, (\d+)e, (\d+)w c?e?x?k?d?b?-$')
    def prompt(self, match, realm):
        """Look at all the herbs we've seen, and harvest one of them if we
        are harvesting.
        """
        if self.harvesting:
            if self.herbs_in_room:
                herb = self.herbs_in_room.pop()
                realm.send("harvest %s" % herb)
                realm.send("inr %s" % herb)
            elif self.seen_herbs:
                realm.write("All done!")
        self.herbs_in_room = set()
        self.seen_herbs = False

    @binding_alias('^harvest (on|off)$')
    def harvest(self, match, realm):
        """Turn harvesting on or off."""
        realm.send_to_mud = False
        if match.group(1) == 'off':
            self.harvesting = False
        else:
            self.harvesting = True
            realm.send("plants")

#pylint: enable-msg=W0613
