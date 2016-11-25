#coding: utf-8

import re
import json
import urllib
import datetime

from mudpyl.aliases import non_binding_alias, binding_alias
from mudpyl.triggers import non_binding_trigger, binding_trigger, RegexTrigger
from mudpyl.gui.keychords import from_string
from mudpyl.modules import BaseModule
from mudpyl.colours import fg_code, bg_code, BLACK, WHITE, HexFGCode, BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE
from mudpyl.metaline import Metaline, simpleml

OBJ_URL = 'http://mudportal.ru/objects/obj_json/%s/'
OBJ_ADD = 'http://mudportal.ru/objects/add_json/'

RE_BAZ_NEW = re.compile(ur'^Базар : новый лот \((\d+)\) - ([\w\s\-\"]+) - цена (\d+)', re.UNICODE)

OBJ_RES = [
    # железный сундук  <великолепно> (есть содержимое)
    # доспех безликого убийцы  <очень хорошо>
    re.compile(ur'([\w\s\-\"]+)\s*\(?[\w\s]*\)?\s*<[\w\s]+>\s*\(?[\w\s]*\)?', re.UNICODE),
    re.compile(ur'([\w\s\-\"]+)\s*\[\d+\]', re.UNICODE),
    re.compile(ur'<[\w\s\-]+>\s*([\w\s\-\"]+)\s*\(?[\w\s]*\)?\s*<[\w\s]*>', re.UNICODE),
    
    # магаз
    re.compile(ur'\s*\d+\)\s*Навалом\s*([\w\s\-\"]+)\s+\d+', re.UNICODE),
    re.compile(ur'\s*\d+\)\s*\d+\s*([\w\s\-\"]+)\s+\d+', re.UNICODE),

    # базар
    re.compile(ur'\[[\s\d]+\]\s+([\w\s\-\"]+)\s+\d+', re.UNICODE),
    re.compile(ur'^Базар : новый лот \(\d+\) - ([\w\s\-\"]+) - цена \d+', re.UNICODE),
    
    # аук
    re.compile(ur'^Аукцион : новый лот \d - ([\w\s\-\"]+) - начальная ставка \d+', re.UNICODE),
    re.compile(ur'^Аукцион : лот \d\(([\w\s\-\"]+)\),', re.UNICODE),
    re.compile(ur'^Аукцион : лот  \d - ([\w\s\-\"]+) - ставка \d+', re.UNICODE),

    ]


class ObjectsSystem(BaseModule):
    
    def __init__(self, factory):
        BaseModule.__init__(self, factory)
        
        self.opozn_flag = False
        self.parse_flag = False
        
        self.obj_name = ''
        self.obj_desc = ''
        
        self.baz_log = file('baz.log', 'a')
        
        try:
            self.load('objs.json')
        except:
            self.objs = {}
    
    

    @property
    def triggers(self):
        return [self.opozn, self.empty, self.anyline, self.parse1, self.parse2, self.parse3, self.parse4, self.parse5, self.parse6, self.obj_name, ]
    
    @binding_trigger(u'^Вы узнали следующее:')
    def opozn(self, match, realm):
        self.obj_name = ''
        self.obj_desc = ''
        self.opozn_flag = True
        
    
    @binding_trigger(u'^Вы несете:')
    def parse1(self, match, realm):
        self.parse_flag = True
    
    @binding_trigger(u'^На вас надето:')
    def parse2(self, match, realm):
        self.parse_flag = True
    
    @binding_trigger(u'\s*Лот\s+Предмет\s+Цена\s+Состояние')
    def parse3(self, match, realm):
        self.parse_flag = True
        
    @binding_trigger(u'\s*##\s+Доступно\s+Предмет\s+Цена\s*\(куны\)')
    def parse4(self, match, realm):
        self.parse_flag = True
    
    @binding_trigger(u'^Базар : новый лот', sequence = 0)
    def parse5(self, match, realm):
        self.parse_flag = True
    
    @binding_trigger(u'^Аукцион :', sequence = 0)
    def parse6(self, match, realm):
        print 'AAAAA'
        self.parse_flag = True
        
    
    @binding_trigger(u'\d+H \d+M \d+о .*>')
    def empty(self, match, realm):
        if self.opozn_flag:
            print self.obj_desc
            #self.update_obj(self.obj_name, {'desc': self.obj_desc})
            print self.has_obj(self.obj_name)
            if not self.has_obj(self.obj_name):
                v = json.loads(self.add_to_mudportal(self.obj_desc))
                print v
                realm.parent.info(v['message'])
        
        self.opozn_flag = False
        self.parse_flag = False
    
    
    @binding_trigger(u'(.*)', sequence = 10)
    def anyline(self, match, realm):
        if self.opozn_flag:
            s = match.group(1).strip()
            if s != '':
                self.obj_desc = '%s\n%s' % (self.obj_desc, s)
        
        if self.parse_flag:
            
            # logging baz
            m = RE_BAZ_NEW.match(match.group(1))
            print m, match.group(1)
            if m:
                w = {
                    'lot': m.group(1).strip(),
                    'object': m.group(2).strip(),
                    'price': m.group(3).strip(),
                    'date': '%s' % datetime.datetime.now(),
                    }
                self.baz_log.write('%s\n' % json.dumps(w, encoding="utf-8"))
                self.baz_log.flush()
            
            print 'PPPPP', match.group(1).strip()
            for res in OBJ_RES:
                m = res.match(match.group(1))
                if m:
                    o = m.group(1).strip()
                    if not self.has_obj(o):
                        print 'Getting from mudportal'
                        desc = self.get_from_mudportal(o)
                        if desc != {}:
                            self.update_obj(o, desc)
                    print o
                    if self.has_obj(o):
                        realm.alterer.insert_metaline(m.start(1) + len(o) + 1, self.obj_as_metaline(o))
                    else:
                        metaline = simpleml('(?)', fg_code(RED, True), bg_code(BLACK))
                        realm.alterer.insert_metaline(m.start(1) + len(o) + 1, metaline)
    
    def obj_as_metaline(self, o):
        desc = self.objs[o]
        print desc.keys()
        colour = HexFGCode(0xFF, 0xAA, 0x00)
        metaline = simpleml('(', colour, bg_code(BLACK))
        metaline += simpleml(desc['type'], colour, bg_code(BLACK))
        
        if desc['weapon'] and desc['weapon'] != 'None':
            metaline += simpleml(',' + desc['weapon'], fg_code(YELLOW, True), bg_code(BLACK))
            metaline += simpleml(',' + desc['dmg_str'], fg_code(RED, True), bg_code(BLACK))
            metaline += simpleml(',' + '%s' % desc['dmg_avg'], fg_code(RED, True), bg_code(BLACK))
            
        if desc['ac']:
            metaline += simpleml(',AC:%s' % desc['ac'], fg_code(RED, True), bg_code(BLACK))
        
        if desc['prop'] != '':
            metaline += simpleml(',' + desc['prop'], fg_code(BLUE, True), bg_code(BLACK))
        
        metaline += simpleml(')', colour, bg_code(BLACK))
        return metaline
        
    
    @binding_trigger(ur'Предмет "([\w\s]+)", тип :')
    def obj_name(self, match, realm):
        if self.opozn_flag:
            self.obj_name = match.group(1).strip()
    
    def has_obj(self, o):
        return o in self.objs.keys()
    
    def update_obj(self, obj, desc):
        self.objs[obj] = desc
        
        self.dump('objs.json')
    
    def dump(self, path):
        file(path, 'w').write(json.dumps(self.objs, encoding="utf-8"))
        
    def load(self, path):
        self.objs = json.loads(file(path, 'r').read(), encoding="utf-8")
    
    def get_from_mudportal(self, o):
        return json.load(urllib.urlopen((OBJ_URL % o).encode('utf-8')), encoding="utf-8")
    
    def add_to_mudportal(self, desc):
        data = urllib.urlencode({'data': desc,})
        c = urllib.urlopen(OBJ_ADD, data)
        return c.read()

