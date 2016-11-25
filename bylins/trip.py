#coding: utf-8

from mudpyl.aliases import non_binding_alias, binding_alias
from mudpyl.triggers import non_binding_trigger, binding_trigger, RegexTrigger
from mudpyl.gui.keychords import from_string
from mudpyl.modules import BaseModule
from mudpyl.colours import *
from mudpyl.metaline import Metaline, simpleml
import re
import json

class TripSystem(BaseModule):
    def __init__(self, factory):
        BaseModule.__init__(self, factory)
