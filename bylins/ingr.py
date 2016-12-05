#coding: utf-8

import re
import json
import urllib
import datetime
import csv

from mudpyl.aliases import non_binding_alias, binding_alias
from mudpyl.triggers import non_binding_trigger, binding_trigger, RegexTrigger
from mudpyl.gui.keychords import from_string
from mudpyl.modules import BaseModule
from mudpyl.colours import fg_code, bg_code, BLACK, WHITE, HexFGCode, BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE
from mudpyl.metaline import Metaline, simpleml

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

class IngrSystem(BaseModule):
    
    sequence = 0
    
    def __init__(self, factory, re_ingr_file = 're_ingr.csv'):
        BaseModule.__init__(self, factory)
        
        self.realm = factory
        
        self.re_ingr_file = re_ingr_file
        self.update_res()
        

    @property
    def triggers(self):
        return [self, ]

    @property
    def aliases(self):
        return [self.do_update_res,]
    
    def __call__(self, match, realm):
        realm.trace_thunk(lambda: "%s matched!" % self)
        cmd = u'взя все.%s\n пол все.%s сум_ингр' % (match, match)
        realm.write(cmd)
        realm.send(cmd)
    
    def match(self, metaline):
        for i in self.res.keys():
            if i.match(metaline.line):
                return [self.res[i][1], ]
        return []

    @binding_alias(u'^_ингр_ре')
    def do_update_res(self, match, realm):
        realm.send_to_mud = False
        self.update_res()
    
    def update_res(self):
        self.realm.write_c(u'Обновление регулярок для ингридиентов:', GREEN)
        f = unicode_csv_reader(open(self.re_ingr_file), delimiter=':')
        self.res = {}
        for row in f:
            if len(row) > 1:
                self.res[re.compile(ur'%s' % row[0])] = row
                self.realm.write_c(u'%s' % (', '.join(row)), GREEN)
        