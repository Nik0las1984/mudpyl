"""A prompt-timestamper, for Achaea."""
from mudpyl.triggers import non_binding_trigger
from mudpyl.colours import HexFGCode, bg_code, BLACK
from mudpyl.metaline import simpleml
from datetime import datetime

@non_binding_trigger("^\d+h, \d+m, \d+e, \d+w( )c?e?x?k?d?b?-")
def prompt_time_display(match, realm):
    """Add a pink coloured timestamp to the prompt."""
    now = datetime.now()
    metaline = simpleml((now.strftime("(%H:%M:%S.%%s) ") %
                                                  str(now.microsecond)[:2]),
                        HexFGCode(0xFF, 0xA0, 0xA0), bg_code(BLACK))
    realm.alterer.insert_metaline(match.end(1), metaline)
