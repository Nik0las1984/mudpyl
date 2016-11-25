#coding: utf-8

from mudpyl.aliases import non_binding_alias, binding_alias
from mudpyl.triggers import non_binding_trigger, binding_trigger, RegexTrigger
from mudpyl.gui.keychords import from_string
from mudpyl.modules import BaseModule
from mudpyl.colours import *
import json


class MapperSystem(BaseModule):
    def __init__(self, factory):
        BaseModule.__init__(self, factory)
        self.show_trigs_flag = True
        self.map_trigs = {}
        self.m = factory.mmap
        self.realm = factory
        
        self.m.add_listener(self)
        
        try:
            self.load('trigs.json')
        except:
            self.map_trigs = {}
        
        self.tcnt = 0
        
        
        # телепорты
        try:
            self.load_teleports('teleports.json')
        except:
            self.teleports = {}
        
        self.teleport_curr = None
        self.teleport_flag = False
    
    
    def load_teleports(self, path):
        self.teleports = json.loads(file(path, 'r').read(), encoding="utf-8")
    
    def dump_teleports(self, path):
        file(path, 'w').write(json.dumps(self.teleports, encoding="utf-8"))

    @property
    def macros(self):
        return {from_string('C-<cyrillic_ie>'): self.do_trig,}
    
    def do_trig(self, realm):
        r = self.m.last_room
        if not r:
            self.realm.info(u'Неправильная комната', fg_code(GREEN, True))
            return
        if not self.map_trigs.has_key(r.vnum):
            self.realm.info(u'Нет триггеров', fg_code(GREEN, True))
            return
        t = self.map_trigs[r.vnum]
        self.realm.info(u'Делаем триг %s: %s' % (self.tcnt, t[self.tcnt][1]), fg_code(GREEN, True))
        realm.send(t[self.tcnt][1])
        self.tcnt += 1
        if self.tcnt >= len(t):
            self.tcnt = 0
    
    def load(self, path):
        self.map_trigs = json.loads(file(path, 'r').read(), encoding="utf-8")
    
    def dump(self, path):
        file(path, 'w').write(json.dumps(self.map_trigs, encoding="utf-8"))
    
    @property
    def triggers(self):
        return []

    @property
    def aliases(self):
        return [
                self.mapper,
                self.mapper_where,
                self.mapper_dump,

                self.mapper_trig,
                self.mapper_trig_add,
                self.mapper_trig_del,

                self.teleport,
                self.teleport_add,
                self.teleport_del,
                ]
    
    @binding_alias(u'^_маппер$')
    def mapper(self, match, realm):
        realm.parent.telnet.msdp.msdp_request('REPORT'.encode('utf-8'), 'ROOM'.encode('utf-8'))
        realm.parent.telnet.msdp.msdp_request('SEND'.encode('utf-8'), 'ROOM'.encode('utf-8'))
        realm.send_to_mud = False
    
    @binding_alias(u'^_маппер_гдея$')
    def mapper_where(self, match, realm):
        m = realm.parent.mmap
        r = m.last_room
        if r:
            realm.parent.info(u'%s[%s] (%s[%s])' % (r.name, r.vnum, r.area, r.zone))
        realm.send_to_mud = False
    
    @binding_alias(u'^_маппер_дамп$')
    def mapper_dump(self, match, realm):
        m = realm.parent.mmap
        m.save()
        realm.parent.info(u'Карта сохранена')
        realm.send_to_mud = False
    
    @binding_alias(u'^_триг$')
    def mapper_trig(self, match, realm):
        self.print_trigs(self.m.last_room)
        realm.send_to_mud = False
        
    
    @binding_alias(u'^_триг (.*) _ (.*)$')
    def mapper_trig_add(self, match, realm):
        self.add_trig(match.group(1), match.group(2), self.m.last_room)
        self.print_trigs(self.m.last_room)
        realm.send_to_mud = False
    
    @binding_alias(u'^_триг_удал (\d+)$')
    def mapper_trig_del(self, match, realm):
        self.del_trig(int(match.group(1)), self.m.last_room)
        self.print_trigs(self.m.last_room)
        realm.send_to_mud = False

    def del_trig(self, n, r):
        if not r:
            return
        if not self.map_trigs.has_key(r.vnum):
            self.map_trigs[r.vnum] = []
        t = self.map_trigs[r.vnum]
        if n > len(t) - 1:
            self.realm.info(u'Нет такого номера', fg_code(GREEN, True))
            return
        del t[n]
        self.realm.info(u'Триггер удален', fg_code(GREEN, True))
        
        self.dump('trigs.json')
    
    def add_trig(self, t, t1, r):
        if not r:
            return
        if not self.map_trigs.has_key(r.vnum):
            self.map_trigs[r.vnum] = []
        self.map_trigs[r.vnum].append((t, t1))
        self.realm.info(u'Триггер добавлен', fg_code(GREEN, True))
        self.dump('trigs.json')
            
    
    def print_trigs(self, r):
        if r and self.map_trigs.has_key(r.vnum):
            t = self.map_trigs[r.vnum]
            for i in range(len(t)):
                self.realm.info('%s. %s -> %s' % (i, t[i][0], t[i][1]), fg_code(GREEN, True))
        else:
            self.realm.info('Нет триггеров')
        
    def on_room(self, r):
        self.tcnt = 0
        if self.show_trigs_flag and self.map_trigs.has_key(r.vnum):
            self.print_trigs(r)
            
        if self.teleports.has_key(r.vnum):
            self.print_teleports(r)
        
        
        if self.teleport_flag:
            self.add_teleport(self.teleport_curr[2], r.vnum, self.teleport_curr[0], self.teleport_curr[1])
            self.print_teleports(r)
        self.teleport_flag = False
    
    
    
    @binding_alias(u'^_телепорт$')
    def teleport(self, match, realm):
        self.print_teleports(self.m.last_room)
        realm.send_to_mud = False
        
    
    @binding_alias(u'^_телепорт (.*) _ (.*)$')
    def teleport_add(self, match, realm):
        self.teleport_curr = [match.group(1), match.group(2), self.m.last_room]
        self.teleport_flag = True
        realm.send_to_mud = False
    
    @binding_alias(u'^_телепорт_удал (\d+)$')
    def teleport_del(self, match, realm):
        self.del_teleport(int(match.group(1)), self.m.last_room)
        self.print_teleports(self.m.last_room)
        realm.send_to_mud = False

    def del_teleport(self, n, r):
        if not r:
            return
        if not self.teleports.has_key(r.vnum):
            self.teleports[r.vnum] = []
        t = self.teleports[r.vnum]
        if n > len(t) - 1:
            self.realm.info(u'Нет такого номера', fg_code(BLUE, True))
            return
        del t[n]
        self.realm.info(u'Телепорт удален', fg_code(BLUE, True))
        
        self.dump_teleports('teleports.json')
    
    def add_teleport(self, fr, to, cmd, h):
        if not fr:
            return
        if not self.teleports.has_key(fr.vnum):
            self.teleports[fr.vnum] = []
        self.teleports[fr.vnum].append((to, cmd, h))
        self.realm.info(u'Телепорт добавлен', fg_code(BLUE, True))
        self.dump_teleports('teleports.json')
            
    
    def print_teleports(self, r):
        if r and self.teleports.has_key(r.vnum):
            t = self.teleports[r.vnum]
            for i in range(len(t)):
                to = self.m.rooms[t[i][0]]
                self.realm.info('%s. %s -> %s (%s)' % (i, to.area, t[i][2], t[i][1]), fg_code(BLUE, True))
        else:
            self.realm.info('Нет телепортов')

    