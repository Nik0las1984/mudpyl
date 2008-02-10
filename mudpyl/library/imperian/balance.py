"""A balance highlighter.

For: Imperian.
"""
from mudpyl.triggers import non_binding_trigger
from mudpyl.colours import HexFGCode

#The unused arguments are harmless.
#pylint: disable-msg=W0613

@non_binding_trigger("^You have recovered balance\.$")
def balance_highlight(match, realm):
    """When we get balance back, set it to a garish green."""
    realm.alterer.change_fore(0, match.end(), HexFGCode(0x80, 0xFF, 0x80))

#pylint: enable-msg=W0613
