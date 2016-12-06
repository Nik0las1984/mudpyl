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

RE_INGR1 = re.compile(ur'^(.+?)  <.+>$', re.UNICODE)
RE_INGR2 = re.compile(ur'^(.+?) \[(\d+)\]$', re.UNICODE)

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
    
    def __init__(self, factory, re_ingr_file = 're_ingr.csv', db_ingr_file = 'db_ingr.csv'):
        BaseModule.__init__(self, factory)
        
        self.realm = factory
        
        self.re_ingr_file = re_ingr_file
        self.update_res()
        
        self.db_ingr_file = db_ingr_file
        self.update_ingr_db()
        
        self.recipes = {}
        self.parse_recipes_flag = False
        self.parse_recipe_flag = False
        self.cur_recipe = []
        
        self.load_ingr_flag = False
        self.ingrs = {}
        

    @property
    def triggers(self):
        return [self,
                self.on_normal_status,
                self.on_recipes,
                self.on_recipe,
                self.on_load_ingr,
                ]

    @property
    def aliases(self):
        return [
                self.do_update_res,
                self.do_update_recipes,
                self.do_recipes,
                self.do_load_ingr,
                self.do_recipes_varka,
                ]
    
    @binding_trigger(RE_NORMAL_STATUS)
    def on_normal_status(self, match, realm):
        if self.parse_recipes_flag:
            self.realm.write_c(u'Загружены рецепты:', GREEN)
            for r in self.recipes.keys():
                self.realm.write_c(u'Рецепт: %s' % r, GREEN)
                self.realm.send(u'сост рец !%s!' % r)
        
        
        if self.load_ingr_flag:
            self.realm.write_c(u'Загружены ингридиенты:', GREEN)
            for i in self.ingrs.keys():
                self.realm.write_c(u'%s - %s' % (i, len(self.ingrs[i])), GREEN)
        
        self.parse_recipes_flag = False
        self.parse_recipe_flag = False
        self.load_ingr_flag = False
    
    @binding_trigger(u'^Вы владеете следующими рецептами :')
    def on_recipes(self, match, realm):
        self.parse_recipes_flag = True
        #self.realm.write_c(u'Парсим рецепты.', GREEN)
        realm.send_to_mud = False
    
    def recipe_varka(self, r, num):
        for cnt in range(num):
            cmd = u'варить !%s!' % r
            for i in self.recipes[r]:
                #self.realm.write(u'взя %s сум_инг' % i)
                g = self.get_ingr(i)
                if g:
                    self.realm.send(u'взя %s сум_инг' % g)
                else:
                    return
                
                cmd = '%s %s' % (cmd, g)
            #self.realm.write(cmd)
            self.realm.send(cmd)
    
    def get_ingr(self, ing):
        if self.ingrs.has_key(ing):
            i = self.ingrs[ing]
            if len(i) == 0:
                self.realm.write_c(u'Нет ингридиента "%s", попробуйте _ингр_загрузить.' % ing, RED)
                return None
            else:
                return i.pop().replace(u' ', u'.')
        else:
            self.realm.write_c(u'Нет ингридиента "%s", попробуйте _ингр_загрузить.' % ing, RED)
            return None
            
    
    def __call__(self, match, realm):
        realm.trace_thunk(lambda: "%s matched!" % self)
        cmd = u'взя все.%s\n пол все.%s сум_ингр' % (match, match)
        realm.write(cmd)
        realm.send(cmd)
    
    def match(self, metaline):
        # Парсим список рецептов
        if self.parse_recipes_flag:
            m = RE_RECIPE.match(metaline.line)
            #self.realm.write_c(u'Парсим рецепт %s.' % m, GREEN)
            if m:
                r = m.group(1)
                if not self.recipes.has_key(r):
                    self.recipes[r] = []
        
        # Парсим конкретный рецепт
        if self.parse_recipe_flag:
            m = RE_RECIPE_COMP.match(metaline.line)
            if m:
                self.cur_recipe.append(m.group(1))
            m = RE_RECIPE_SOST.match(metaline.line)
            if m:
                self.recipes[m.group(1)] = self.cur_recipe
                self.parse_recipe_flag = False
        
        # Парсим ингры в сумке
        if self.load_ingr_flag:
            ingr_found = False
            m = RE_INGR1.match(metaline.line)
            if m:
                for i in self.db_ingr.keys():
                    if i.match(m.group(1)):
                        ing = self.db_ingr[i][2]
                        if self.ingrs.has_key(ing):
                            self.ingrs[ing].append(m.group(1))
                        else:
                            self.ingrs[ing] = [m.group(1),]
                        ingr_found = True
                if not ingr_found:
                    self.realm.write_c(u'Неизвестный ингридиент: %s' % m.group(1), RED)
            m = RE_INGR2.match(metaline.line)
            if m:
                for i in self.db_ingr.keys():
                    if i.match(m.group(1)):
                        ing = self.db_ingr[i][2]
                        a = []
                        for i in range(int(m.group(2))):
                            a.append(m.group(1))
                        if self.ingrs.has_key(ing):
                            self.ingrs[ing] += a
                        else:
                            self.ingrs[ing] = a
                        ingr_found = True
                if not ingr_found:
                    self.realm.write_c(u'Неизвестный ингридиент: %s' % m.group(1), RED)
        # Проверяем регулярки на ингры
        for i in self.res.keys():
            fores = metaline.fores
            r = self.res[i]
            if len(r) > 2:
                c = map(int, r[2].split(u','))
                if len(fores) == 1:
                    if fores[0] == HexFGCode(c[0], c[1], c[2]) and i.match(metaline.line):
                        return [self.res[i][1], ]
            elif i.match(metaline.line):
                return [self.res[i][1], ]
        return []
    
    @binding_trigger(u'^Ваши метки: сум ингр')
    def on_load_ingr(self, match, realm):
        realm.send_to_mud = False
        if self.load_ingr_flag:
            self.ingrs = {}
            self.realm.write_c(u'Загружаем ингры', GREEN)
    
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
        self.update_ingr_db()
    
    @binding_alias(u'^_ингр_загрузить')
    def do_load_ingr(self, match, realm):
        self.load_ingr_flag = True
        realm.send_to_mud = False
        realm.write(u'осм сум_ингр')
        realm.send(u'осм сум_ингр')
    
    @binding_alias(u'^_рец_обновить')
    def do_update_recipes(self, match, realm):
        realm.send_to_mud = False
        self.recipes = {}
        realm.write(u'рец')
        realm.send(u'рец')
    
    @binding_alias(u'^_рец_варить (\d+)')
    def do_recipes_varka(self, match, realm):
        realm.send_to_mud = False
        rn = int(match.group(1))
        cnt = 1
        svaren = False
        for r in self.recipes.keys():
            if cnt == rn:
                self.recipe_varka(r, 1)
                svaren = True
            cnt += 1
        if not svaren:
            self.realm.write_c(u'Рецепт %s не найден!' % rn, RED)
    
    
    def calc_recipe(self, r):
        v = 1000000
        for ing in r:
            if self.ingrs.has_key(ing):
                v = min(v, len(self.ingrs[ing]))
            else:
                return 0
        return v
    
    @binding_alias(u'^_рец$')
    def do_recipes(self, match, realm):
        realm.send_to_mud = False
        cnt = 1
        for r in self.recipes.keys():
            self.realm.write_c(u'%s. "%s" (%s) - %s штук' % (cnt, r, ', '.join(self.recipes[r]), self.calc_recipe(self.recipes[r])), GREEN)
            cnt += 1

    def update_res(self):
        self.realm.write_c(u'Обновление регулярок для ингридиентов:', GREEN)
        f = unicode_csv_reader(open(self.re_ingr_file), delimiter=':')
        self.res = {}
        for row in f:
            if len(row) > 1:
                self.res[re.compile(ur'%s' % row[0])] = row
                self.realm.write_c(u'%s' % (', '.join(row)), GREEN)
    
    def update_ingr_db(self):
        self.realm.write_c(u'Обновление базы ингридиентов:', GREEN)
        f = unicode_csv_reader(open(self.db_ingr_file), delimiter=':')
        self.db_ingr = {}
        for row in f:
            if len(row) > 1:
                self.db_ingr[re.compile(ur'%s' % row[1])] = row
                self.realm.write_c(u'%s' % (', '.join(row)), GREEN)
        