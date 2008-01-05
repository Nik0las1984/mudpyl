"""Some general helpful stuff."""
from mudpyl.aliases import non_binding_alias
from mudpyl.gui.keychords import from_string

#pylint doesn't like that func is set in __init__ too, if the conditions are
#right. Also, the unused arguments are harmless.
#pylint: disable-msg=E0202,W0613

@non_binding_alias('^#repeat (\d+) (.*)$')
def repeat(match, realm):
    """Repeats a given command a given number of times."""
    for _ in xrange(int(match.group(1))):
        realm.send(match.group(2))
    realm.send_to_mud = False

#pylint: enable-msg=E0202

def trace_toggle(realm):
    """Turn tracing on or off, depending on its current state."""
    if not realm.tracing:
        realm.trace_on()
    else:
        realm.trace_off()

def keypad_move(direction):
    """A wrapper to stop me having loads of different direction-moving
    functions.
    """
    def walker(realm):
        """Actually send the direction."""
        realm.send(direction)
    return walker

#pylint: enable-msg= W0613

keypad_directions = {from_string('<numpad 7>'): keypad_move('nw'),
                     from_string('<numpad 8>'): keypad_move('n'),
                     from_string('<numpad 9>'): keypad_move('ne'),
                     from_string('<numpad 4>'): keypad_move('w'),
                     from_string('<numpad 6>'): keypad_move('e'),
                     from_string('<numpad 1>'): keypad_move('sw'),
                     from_string('<numpad 2>'): keypad_move('s'),
                     from_string('<numpad 3>'): keypad_move('se'),
                     from_string('<numpad divide>'): keypad_move('in'),
                     from_string('<numpad multiply>'): keypad_move('out'),
                     from_string('<numpad subtract>'): keypad_move('up'),
                     from_string('<numpad add>'): keypad_move('down')}
