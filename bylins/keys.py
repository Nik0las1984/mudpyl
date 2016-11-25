#coding: utf-8

from mudpyl.aliases import non_binding_alias, binding_alias
from mudpyl.triggers import non_binding_trigger, binding_trigger
from mudpyl.gui.keychords import from_string
from mudpyl.modules import BaseModule

def keypad_move(direction):
    """A wrapper to stop me having loads of different direction-moving
    functions.
    """
    def walker(realm):
        realm.set_var(u'направление', direction, False)
        """Actually send the direction."""
        d = direction
        if realm.get_var(u'автосник'):
            d = 'краст %s\nспрят' % direction
        realm.send(d)
    return walker

def merge_dicts(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

def toggle_auto_snik():
    def toggle(realm):
        realm.toggle_var(u'автосник')
    return toggle

def keypad(k):
    def do(realm):
        realm.send(k)
    return do

class KeysSystem(BaseModule):
    keypad_directions = {
                        from_string('<numpad 7>'): keypad_move('up'),
                        from_string('<numpad 8>'): keypad_move('n'),
                        from_string('<numpad 4>'): keypad_move('w'),
                        from_string('<numpad 6>'): keypad_move('e'),
                        from_string('<numpad 1>'): keypad_move('down'),
                        from_string('<numpad 2>'): keypad_move('s'),
                        }
    keypad_look = {
        from_string('<numpad 5>'): keypad('look \n огл'),
        
        # Побеги и рекол
        from_string('<numpad add>'): keypad('~\nбежать'),
        from_string('C-1'): keypad('~'),
        from_string('C-2'): keypad('~\n зачит возв \n вз возвр сунд1 \n дер офф'),
        from_string('C-3'): keypad('~\n вз возвр сунд1 \n зачит возв \n вз возвр сунд1 \n дер офф'),
        
        # Лутим трупы
        from_string('<numpad subtract>'): keypad('вз все.труп \n вз все все.труп \n бр все.труп'),
        
        from_string('<numpad 0>'): keypad('подн'),
        
        
        # Автосник ы
        from_string(u'C-<cyrillic_yeru>'): toggle_auto_snik(),
        }
    
    keys = merge_dicts(keypad_directions, keypad_look)
    
    def __init__(self, factory):
        BaseModule.__init__(self, factory)
    

    @property
    def macros(self):
        return self.keys
        

