from mudpyl.triggers import non_binding_trigger
from mudpyl.colours import HexFGCode
from datetime import datetime

@non_binding_trigger("^\d+h, \d+m, \d+e, \d+w( )c?e?x?k?d?b?-")
def prompt_time_display(match, realm):
    now = datetime.now()
    realm.alterer.insert(match.end(1), now.strftime("(%H:%M:%S.%%s) ") %
                                              str(now.microsecond)[:2])
    realm.alterer.change_fore(match.start(1), match.end(1),
                              HexFGCode(0xFF, 0xA0, 0xA0)) #lovely pink
