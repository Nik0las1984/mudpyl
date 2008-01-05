"""Keeps track of your rift and tells you what you can make.

For: Achaea.
"""
from peak.util.extremes import Max
from mudpyl.modules import BaseModule
from mudpyl.triggers import binding_trigger
from mudpyl.aliases import binding_alias
from mudpyl.library.refiller import ingredients
from copy import deepcopy

ingredients = deepcopy(ingredients)
#we don't store gold in the rift, so we can't check it.
while 'gold' in ingredients['restoration']:
    ingredients['restoration'].remove('gold')

riftnames = {'ginseng root': 'ginseng',
             'valerian': 'valerian',
             'goldenseal root': 'goldenseal',
             'myrrh gum': 'myrrh',
             'hawthorn berry': 'hawthorn',
             'bellwort flower': 'bellwort',
             'bloodroot leaf': 'bloodroot',
             "lady's slipper": 'slipper',
             'kuzu root': 'kuzu',
             'echinacea': 'echinacea',
             'venom sac': 'sac',
             'prickly ash bark': 'ash',
             'black cohosh': 'cohosh',
             'kelp': 'kelp',
             'skullcap': 'skullcap',
             'prickly pear': 'pear',
             "eagle's feather": 'feather',
             'diamond dust': 'dust',
             'ginger root': 'ginger',
             'irid moss': 'moss',
             'sidewinder skin': 'skin'}

def flatten(seq):
    """Concatenate a list of lists into a single list."""
    for seq2 in seq:
        for obj in seq2:
            yield obj

def reverse(dictionary):
    """Turns a dictionary with lists of values around.

    Example:
        >>> reverse({1: ['foo', 'bar'], 2: ['bar', 'baz']}
        {'foo': [1], 'bar': [1, 2], 'baz': [2]}
    """
    res = dict((val, set()) for val in flatten(dictionary.values()))
    for key in dictionary:
        for val in dictionary[key]:
            res[val].add(key)
    return res

makes = reverse(ingredients)

herbs = set(makes.keys())

class RiftTracker(BaseModule):
    """A module to track what can be made from your rift."""

    def __init__(self, factory):
        BaseModule.__init__(self, factory)
        self.herbs_seen = None
        self.looking_for_herbs = None
        self.max_vials = None
        self.bottlenecks = None
        self._reset()

    def _reset(self):
        """Put our instance variables back to their defaults."""
        self.herbs_seen = dict((herb, 0) for herb in herbs)
        self.looking_for_herbs = False
        self.max_vials = dict((vial, Max) for vial in ingredients)
        self.bottlenecks = dict((vial, set()) for vial in ingredients)

    @property
    def triggers(self):
        """The triggers we want added."""
        return [self.herb_trigger, self.prompt_trigger]

    @property
    def aliases(self):
        """The aliases we want added."""
        return [self.info_rift_alias]

    def count_vials(self):
        """Do the number crunching."""
        for herb in herbs:
            num = self.herbs_seen[herb]
            for vial in makes[herb]:
                factor = ingredients[vial].count(herb)
                possible = num // (factor * 4)
                if possible < self.max_vials[vial]:
                    self.max_vials[vial] = possible
                    self.bottlenecks[vial] = set([herb])
                elif possible == self.max_vials[vial]:
                    self.bottlenecks[vial].add(herb)

    #ignore unused variables in function signatures
    #pylint: disable-msg=W0613

    @binding_trigger('\[ *(\d+)\] *(%s)' % '|'.join(riftnames.keys()))
    def herb_trigger(self, match, realm):
        """We've spotted one herb in our rift."""
        if not self.looking_for_herbs:
            return
        num = int(match.group(1))
        herb = riftnames[match.group(2)]
        self.herbs_seen[herb] = num

    @binding_trigger('^\d+h, \d+m, \d+e, \d+w c?e?x?k?d?b?@?-$')
    def prompt_trigger(self, match, realm):
        """A prompt's been received; the rift listing is over."""
        if not self.looking_for_herbs:
            return
        self.count_vials()
        for vial in ingredients:
            realm.write('%s: %d vials. Bottleneck: %s' % 
                        (vial, self.max_vials[vial], 
                         ' and '.join(self.bottlenecks[vial])))
        self._reset()

    @binding_alias('^ir$')
    def info_rift_alias(self, match, realm):
        """We want to peek inside the rift."""
        self.looking_for_herbs = True

