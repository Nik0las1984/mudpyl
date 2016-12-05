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

RE_NORMAL_STATUS = ur'^\d+H \d+M \d+о Зауч:\d+ .*\d+L \d+G Вых:.*>'

RE_RECIPE = re.compile(ur'^(.+?)\s+\(.+\)\s*\d%$', re.UNICODE)

RE_RECIPE_SOST = re.compile(ur'^для приготовления отвара \'(.+?)\'', re.UNICODE)
RE_RECIPE_COMP = re.compile(ur'^\d+\) (.+?)$')

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
        
        self.recipes = {}
        self.parse_recipes_flag = False
        self.parse_recipe_flag = False
        self.cur_recipe = []
        

    @property
    def triggers(self):
        return [self,
                self.on_normal_status,
                self.on_recipes,
                self.on_recipe,
                ]

    @property
    def aliases(self):
        return [
                self.do_update_res,
                self.do_update_recipes,
                self.do_recipes,
                ]
    
    @binding_trigger(RE_NORMAL_STATUS)
    def on_normal_status(self, match, realm):
        if self.parse_recipes_flag:
            self.realm.write_c(u'Загружены рецепты:', GREEN)
            for r in self.recipes.keys():
                self.realm.write_c(u'Рецепт: %s' % r, GREEN)
                self.realm.send(u'сост рец !%s!' % r)
        self.parse_recipes_flag = False
        self.parse_recipe_flag = False
    
    @binding_trigger(u'^Вы владеете следующими рецептами :')
    def on_recipes(self, match, realm):
        self.parse_recipes_flag = True
        #self.realm.write_c(u'Парсим рецепты.', GREEN)
        realm.send_to_mud = False
    
    def __call__(self, match, realm):
        realm.trace_thunk(lambda: "%s matched!" % self)
        cmd = u'взя все.%s\n пол все.%s сум_ингр' % (match, match)
        realm.write(cmd)
        realm.send(cmd)
    
    def match(self, metaline):
        if self.parse_recipes_flag:
            m = RE_RECIPE.match(metaline.line)
            #self.realm.write_c(u'Парсим рецепт %s.' % m, GREEN)
            if m:
                r = m.group(1)
                if not self.recipes.has_key(r):
                    self.recipes[r] = []
        
        if self.parse_recipe_flag:
            m = RE_RECIPE_COMP.match(metaline.line)
            if m:
                self.cur_recipe.append(m.group(1))
            m = RE_RECIPE_SOST.match(metaline.line)
            if m:
                self.recipes[m.group(1)] = self.cur_recipe
                self.parse_recipe_flag = False
        
        for i in self.res.keys():
            if i.match(metaline.line):
                return [self.res[i][1], ]
        return []
    
    @binding_trigger(u'^Вам потребуется :$')
    def on_recipe(self, match, realm):
        self.parse_recipe_flag = True
        self.cur_recipe = []
        #self.realm.write_c(u'Парсим рецепты.', GREEN)
        realm.send_to_mud = False
    
    @binding_alias(u'^_ингр_ре')
    def do_update_res(self, match, realm):
        realm.send_to_mud = False
        self.update_res()
    
    @binding_alias(u'^_рец_обновить')
    def do_update_recipes(self, match, realm):
        realm.send_to_mud = False
        self.recipes = {}
        realm.write(u'рец')
        realm.send(u'рец')
    
    
    @binding_alias(u'^_рец')
    def do_recipes(self, match, realm):
        realm.send_to_mud = False
        for r in self.recipes.keys():
            self.realm.write_c(u'Рецепт: %s (%s)' % (r, ', '.join(self.recipes[r])), GREEN)

    def update_res(self):
        self.realm.write_c(u'Обновление регулярок для ингридиентов:', GREEN)
        f = unicode_csv_reader(open(self.re_ingr_file), delimiter=':')
        self.res = {}
        for row in f:
            if len(row) > 1:
                self.res[re.compile(ur'%s' % row[0])] = row
                self.realm.write_c(u'%s' % (', '.join(row)), GREEN)
        