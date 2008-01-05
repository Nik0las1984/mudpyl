"""A system for refilling vials."""
from mudpyl.triggers import binding_trigger
from mudpyl.aliases import binding_alias
from mudpyl.modules import BaseModule

ingredients = {'immunity': ['sac', 'ash', 'echinacea', 'echinacea'],
                'mana': ['slipper', 'bellwort', 'bloodroot', 'hawthorn'],
                'health': ['myrrh', 'ginseng', 'goldenseal', 'valerian'],
                'venom': ['sac', 'cohosh', 'kelp', 'skullcap'],
                'frost': ['kelp', 'pear', 'ginseng'],
                'caloric': ['kuzu', 'kuzu', 'valerian', 'kelp', 'kelp',
                            'bellwort'],
                'mending': ['dust', 'kelp', 'kuzu', 'ginger', 'ginger'],
                'mass': ['moss', 'bloodroot', 'kuzu', 'dust'],
                'speed': ['skin', 'skin', 'kuzu', 'goldenseal', 'ginger'],
                'epidermal': ['kuzu', 'kuzu', 'bloodroot', 'hawthorn',
                              'ginseng'],
                'levitation': ['kelp', 'kelp', 'pear', 'feather'],
                'restoration': ['gold', 'gold', 'kuzu', 'kuzu', 'valerian',
                                'bellwort']}

class RefillingSystem(BaseModule):
    """Refills vials."""

    def __init__(self, factory):
        super(RefillingSystem, self).__init__(factory)
        self.num = 0
        self.target = None
        self.vial = None

    @property
    def triggers(self):
        """The triggers we need to have added."""
        return [self.made]

    @property
    def aliases(self):
        """The aliases we need to have added."""
        return [self.refill]

#pylint likes complaining about the unused arguments in the callbacks, which
#are actually perfectly harmless.
#pylint: disable-msg=W0613

    @binding_alias('^refill (\d+) (%s) for (\w+)$' % 
                                             '|'.join(ingredients.keys()))
    def refill(self, match, realm):
        """Start the refilling process for a set of vials."""
        num, vial, target = match.groups()
        num = int(num)

        realm.send_to_mud = False

        for herb in ingredients[vial]:
            if herb == 'gold':
                cmd = 'get %d gold from pack' % (num * 4 * 400)
            else:
                cmd = 'outr %d %s' % (num * 4, herb)
            realm.send(cmd) 
            realm.send('inpot %d %s in pot' % (num * 4, herb))

        realm.send("drop pot")
        realm.send("boil pot for %s" % vial)

        self.num = num
        self.vial = vial
        self.target = target

    @binding_trigger("^With a sudden slow pulsing of white light, the liquid"
                      " and floating bits of plant matter in the pot combine "
                     r"into an?(?: (?:salve|elixir) of)? (\w+)(?: salve)?\.$")
    def made(self, match, realm):
        """We've dropped pot and made a concoction. Fill the vials now."""
        vial = match.group(1)
        if vial != self.vial:
            return
        realm.send("get pot")
        for _ in range(self.num):
            realm.send("fill empty from pot 4 times")
            realm.send("give %s to %s" % (self.vial, self.target))
        self.vial = None
        self.target = None

#pylint: enable-msg=W0613
