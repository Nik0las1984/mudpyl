#coding: utf-8

import re
import json
import urllib

from mudpyl.aliases import non_binding_alias, binding_alias
from mudpyl.triggers import non_binding_trigger, binding_trigger, RegexTrigger
from mudpyl.gui.keychords import from_string
from mudpyl.modules import BaseModule
from mudpyl.colours import fg_code, bg_code, BLACK, WHITE, HexFGCode, BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE
from mudpyl.metaline import Metaline, simpleml
import datetime

MUDPORTAL_CHANNEL_URL = 'http://mudportal.ru/channels/add_json/'

class ChannelsLogger(BaseModule):
    
    def __init__(self, factory):
        BaseModule.__init__(self, factory)
        
        self.log = file('channels.log', 'a')
        
    @property
    def triggers(self):
        return [self.bolt, self.scream, self.offtop]
    
    @binding_trigger(u'^([\w\-]*) заметил\w* : (.*)')
    def bolt(self, match, realm):
        m = match.groups()
        self.do_log(m, 1, realm)
    
    @binding_trigger(u'^([\w\-]*) заорал\w* : (.*)')
    def scream(self, match, realm):
        m = match.groups()
        self.do_log(m, 2, realm)
    
    @binding_trigger(u'^\[оффтоп\] ([\w\-]+) : (.*)')
    def offtop(self, match, realm):
        m = match.groups()
        self.do_log(m, 0, realm)
    
    def do_log(self, m, t, realm):
        d = datetime.datetime.now()
        self.log.write('%s\t%s\t%s\t%s\n\n' % (d, t, m[0], m[1]))
        self.log.flush()
        
        v = json.loads(self.add_channel('%s' % d, m[0], m[1], t))
        realm.parent.info(v['message'])

    
    def add_channel(self, date, user, text, type):
        data = urllib.urlencode(
            {'data':
            json.dumps({
            'date': date,
            'user': user,
            'text': text,
            'type': type
            }, encoding="utf-8")
            }
            )
        c = urllib.urlopen(MUDPORTAL_CHANNEL_URL, data)
        return c.read()


