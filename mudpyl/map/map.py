#coding: utf-8
import numpy as np
import json

#http://build-failed.blogspot.ru/2012/11/zoomable-image-with-leaflet.html

MAPFILE = 'map.json'

OPPOSITE_DIRS = {
    u'e': u'w',
    u'w': u'e',
    u'n': u's',
    u's': u'n',
    u'u': u'd',
    u'd': u'u',
    }

DIRS_PLUS = {
    u'e': np.int_([1, 0, 0]),
    u'w': np.int_([-1, 0, 0]),
    u'n': np.int_([0, 1, 0]),
    u's': np.int_([0, -1, 0]),
    u'u': np.int_([0, 0, 1]),
    u'd': np.int_([0, 0, -1]),
    }


def opposite_dir(d):
    return OPPOSITE_DIRS[d]
    

def rotate(A,B,C):
    return (B[0]-A[0])*(C[1]-B[1])-(B[1]-A[1])*(C[0]-B[0])

class Zone:
    def __init__(self, name, vnum, mmap):
        self.name = name
        self.vnum = vnum
        self.mmx = {}
        self.mmy = {}
        self.rooms = {}
        self.mmap = mmap
        
        # Выходы в другие зоны
        self.exits = {}
        
        # Координаты границ
        self.boundary = []
        
        # BBox
        self.bmin = None
        self.bmax = None
        
    
    def update_room(self, r):
        if self.mmx.has_key(r.coords[1]):
            self.mmx[r.coords[1]] = (min(r.coords[0], self.mmx[r.coords[1]][0]), max(r.coords[0], self.mmx[r.coords[1]][1]))
        else:
            self.mmx[r.coords[1]] = (r.coords[0], r.coords[0])
        
        if self.mmy.has_key(r.coords[0]):
            self.mmy[r.coords[0]] = (min(r.coords[1], self.mmy[r.coords[0]][0]), max(r.coords[1], self.mmy[r.coords[0]][1]))
        else:
            self.mmy[r.coords[0]] = (r.coords[1], r.coords[1])
        
        if len(self.rooms) == 0:
            self.bmin = self.bmax = r.coords
        else:
            self.bmin = np.minimum(self.bmin, r.coords)
            self.bmax = np.maximum(self.bmax, r.coords)
        
        self.rooms[r.vnum] = r
        
        #self.construct_boundary()
    
    def get_maxy(self):
        v = None
        for i in self.mmx.keys():
            if v is None:
                v = self.mmx[i][1]
            else:
                v = max(v, self.mmx[i][1])
        return v
    
    def get_avgx(self):
        v = 0
        for i in self.mmy.keys():
            v += self.mmy[i][0] + self.mmy[i][1] 
        return v / len(self.mmy.keys())
    
    def get_avg(self):
        c = None
        for i in self.rooms.values():
            if c is None:
                c = i.coords.copy()
            else:
                c += i.coords
        return c / len(self.rooms.keys())
    
    def check_room(self, r):
        return self.vnum == r.zone
    
    def update_exits(self):
        self.exits = {}
        for r in self.rooms.values():
            for e in r.exits.values():
                r1 = self.mmap.rooms[e]
                if r1.zone is not None and r1.zone != self.vnum:
                    r1.bound_flag = True
                    r.bound_flag = True
                    self.exits[r.vnum] = self.mmap.zones[r1.zone]
                    print self.name, '->', self.exits[r.vnum].name
    
    def check_zone(self, z):
        return z in self.exits.values()
    
    def check_zone_vnum(self, z):
        return self.check_zone(self.mmap.zones[z])
    
    def check_room(self, r):
        return r in self.rooms.values()
    
    def check_not_parsed_room(self, r):
        if r.parsed_flag:
            return False
        for e in r.exits.values():
            if e in self.rooms.keys():
                return True
        return False
    
    def construct_boundary(self):
        self.jarvismarch()
        return
        self.boundary = []
        for i in range(self.bmin[0], self.bmax[0] + 1):
            v = self.bmax[1]
            for r in self.rooms.values():
                if r.coords[0] == i:
                    if r.coords[1] < v:
                        v = r.coords[1]
            self.boundary.append(np.int_([i, v - 1]))
        
        for i in range(self.bmin[1], self.bmax[1] + 1):
            v = self.bmin[0]
            for r in self.rooms.values():
                if r.coords[1] == i:
                    if r.coords[0] > v:
                        v = r.coords[0]
            self.boundary.append(np.int_([v + 1, i]))
        print self.name, self.boundary
    
    def grahamscan(self):
        A = self.rooms.values()
        n = len(A) # число точек
        if n < 3:
            return
        P = range(n) # список номеров точек
        for i in range(1, n):
            if A[P[i]].coords[0]<A[P[0]].coords[0]: # если P[i]-ая точка лежит левее P[0]-ой точки
                P[i], P[0] = P[0], P[i] # меняем местами номера этих точек
        for i in range(2, n): # сортировка вставкой
            j = i
            while j > 1 and (rotate(A[P[0]].coords, A[P[j-1]].coords, A[P[j]].coords) < 0): 
                P[j], P[j-1] = P[j-1], P[j]
                j -= 1
        S = [P[0], P[1]] # создаем стек
        for i in range(2,n):
            while rotate(A[S[-2]].coords, A[S[-1]].coords, A[P[i]].coords) < 0:
                del S[-1] # pop(S)
            S.append(P[i]) # push(S,P[i])
            
        self.boundary = []
        for i in S:
            self.boundary.append(A[i].coords)
            
    def jarvismarch(self):
        A = self.rooms.values()
        n = len(A)
        P = range(n)
        # start point
        for i in range(1, n):
            if A[P[i]].coords[0] < A[P[0]].coords[0]: 
                P[i], P[0] = P[0], P[i]  
        H = [P[0]]
        del P[0]
        P.append(H[0])
        while True:
            right = 0
            for i in range(1,len(P)):
                if rotate(A[H[-1]].coords,A[P[right]].coords,A[P[i]].coords)<0:
                    right = i
            if P[right] == H[0]: 
                break
            else:
                H.append(P[right])
                del P[right]
        
        self.boundary = []
        for i in H:
            self.boundary.append(A[i].coords)
        

class Room:
    def __init__(self, vnum, name = None, area = None, zone = None, exits = {}, terrain = None, parsed_flag = False, coords = np.int_([0, 0, 0])):
        self.name = name
        self.vnum = vnum
        self.area = area
        self.zone = zone
        self.exits = exits
        self.terrain = terrain
        self.parsed_flag = parsed_flag
        self.coords = coords
        #self.dt_flag = False
        #self.slow_dt_flag = False
        #self.yama_flag = False
        
        # Зона граничит с другой
        self.bound_flag = False
        
        # Флаги
        self.flags = set()
    
    def update(self, name = None, area = None, zone = None, exits = {}, terrain = None):
        self.name = name
        self.area = area
        self.zone = zone
        self.update_exits(exits)
        self.terrain = terrain
    
    def update_exits(self, e):
        self.exits.update(e)
    
    def has_neighbour(self, vnum):
        for i in self.exits.keys():
            if self.exits[i] == vnum:
                return i
        return None
    
    def move(self, d):
        self.coords += d
    
    def to_json(self):
        data = {
            'name': self.name,
            'vnum': self.vnum,
            'area': self.area,
            'zone': self.zone,
            'exits': self.exits,
            'terrain': self.terrain,
            'parsed_flag': self.parsed_flag,
            'coords': self.coords.tolist(),
            #'dt_flag': self.dt_flag,
            #'slow_dt_flag': self.slow_dt_flag,
            #'yama_flag': self.yama_flag,
            #'bound_flag': self.bound_flag,
            'flags': list(self.flags),
            }
        return json.dumps(data, encoding="utf-8")
    
    
    def from_json(self, js):
        data = json.loads(js, encoding="utf-8")
        
        self.name = data['name']
        self.vnum = data['vnum']
        self.area = data['area']
        self.zone = data['zone']
        self.exits = data['exits']
        self.terrain = data['terrain']
        self.parsed_flag = data['parsed_flag']
        self.coords = np.int_(data['coords'])
        
        if data.has_key('flags'):
            self.flags = set(data['flags'])
        
        #TODO: remove
        if data.has_key('dt_flag') and data['dt_flag']:
            self.set_flag('dt')
        
        if data.has_key('slow_dt_flag') and data['slow_dt_flag']:
            self.set_flag('slow_dt')
        
        if data.has_key('yama_flag') and data['yama_flag']:
            self.set_flag('yama')
        #self.bound_flag = data.get('bound_flag', False)

    
    def set_flag(self, flag):
        self.flags.add(flag)
    
    def unset_flag(self, flag):
        self.flags.discard(flag)
    
    def has_flag(self, flag):
        return flag in self.flags
    
    def toggle_flag(self, flag):
        if self.has_flag(flag):
            self.unset_flag(flag)
        else:
            self.set_flag(flag)
    
    def toggle_dt(self):
        self.toggle_flag('dt')
    
    def toggle_yama(self):
        self.toggle_flag('yama')
    
    def toggle_slow_dt(self):
        self.toggle_flag('slow_dt')
        

class Map:
    def __init__(self):
        self.rooms  = {}
        self.levels = {}
        self.zones  = {}
        self.gui    = None
        
        self.last_room = None
        
        try:
            self.load(MAPFILE)
        except:
            pass
        if self.gui:
            self.gui.update(r.vnum)
        
        self.listeners = []
    
    def add_listener(self, l):
        self.listeners.append(l)
    
    def msdp_var(self, var):
        if var.has_key('ROOM'):
            r = self.update_room(var['ROOM'])
        
            if self.gui:
                self.gui.update(r)
            for i in self.listeners:
                i.on_room(r)
    
    def save(self):
        self.dump(MAPFILE)
    
    # Дать координаты исходя из последней комнаты
    def coords_from_last_room(self, vnum, exits):
        d = self.last_room.has_neighbour(vnum)
        
        # Ищем в новой
        for i in exits.keys():
            if exits[i] == self.last_room.vnum:
                return self.last_room.coords + DIRS_PLUS[OPPOSITE_DIRS[i]]

        # Ищем в самой комнате
        if d:
            return self.last_room.coords + DIRS_PLUS[d]

        
        return self.last_room.coords + np.int_([1,1,0])
        
    
    def update_room(self, msdp):
        vnum    = unicode(msdp['VNUM'])
        name    = unicode(msdp['NAME'])
        exits   = msdp['EXITS']
        area    = unicode(msdp['AREA'])
        terrain = unicode(msdp['TERRAIN'])
        zone    = unicode(msdp['ZONE'])
        
        exitsu = {}
        for e in exits.keys():
            exitsu[unicode(e)] = unicode(exits[e])
        exits = exitsu
        
        z = self.get_or_create_zone(area, zone)
        
        dump_flag = False
        
        r = None
        if self.has_room(vnum):
            r = self.rooms[vnum]
        else:
            print 'Creating room', vnum
            if self.last_room:
                r = Room(vnum, name, area, zone, exits, terrain, True, self.coords_from_last_room(vnum, exits))
            else:
                r = Room(vnum, name, area, zone, exits, terrain, True)
            self.rooms[vnum] = r
            
            
            level = r.coords[2]
            if self.levels.has_key(level):
                self.levels[level][vnum] = r
            else:
                self.levels[level] = {vnum: r, }
            
            dump_flag = True
            
        print r.name, r.exits    
        
        # Проверяем пропаршена ли она
        if not r.parsed_flag:
            print 'Updating room', vnum
            r.update(name, area, zone, exits, terrain)
            r.parsed_flag = True
            
            dump_flag = True
        
        # Проверяем комнаты по границам
        for e in exits.keys():
            r1 = exits[e]
            d1 = opposite_dir(e)
            
            # Если нет, то добавляем
            if not self.has_room(r1):
                nr = Room(vnum = r1,
                          name = None,
                          area = None,
                          zone = None,
                          exits = {d1: vnum, },
                          terrain = None,
                          parsed_flag = False,
                          coords = r.coords + DIRS_PLUS[e])
                self.rooms[r1] = nr
                
                level = r.coords[2]
                if self.levels.has_key(level):
                    self.levels[level][r1] = nr
                else:
                    self.levels[level] = {r1: nr, }
                
                dump_flag = True

            else:
                nr = self.rooms[r1]
                if not nr.parsed_flag:
                    nr.update_exits({d1: vnum, })
                
                dump_flag = True
        self.last_room = r
        z.update_room(r)
        z.update_exits()
        
        if dump_flag:
            self.dump(MAPFILE)
        
        return r
    
    def add_zone(self, name, vnum):
        z = Zone(name, vnum, self)
        self.zones[vnum] = z
        return z
    
    def has_zone(self, vnum):
        return self.zones.has_key(vnum)
    
    def has_room(self, vnum):
        return self.rooms.has_key(vnum)
    
    def get_or_create_zone(self, name, vnum):
        if self.has_zone(vnum):
            return self.zones[vnum]
        return self.add_zone(name, vnum)
    
    def get_by_coords(self, c, z = None):
        if z:
            for i in self.zones[z].rooms.keys():
                if self.rooms[i].coords[0] == c[0] and self.rooms[i].coords[1] == c[1]:
                    return self.rooms[i]
        for i in self.rooms.keys():
            if self.rooms[i].coords[0] == c[0] and self.rooms[i].coords[1] == c[1] and not self.rooms[i].parsed_flag:
                return self.rooms[i]
        for i in self.rooms.keys():
            if self.rooms[i].coords[0] == c[0] and self.rooms[i].coords[1] == c[1]:
                return self.rooms[i]
        return None
    
    def dump(self, path):
        f = file(path, 'w')
        for i in self.rooms:
            f.write('%s\n' % self.rooms[i].to_json())
        f.close()
    
    def load(self, path):
        self.rooms = {}
        self.zones = {}
        self.levels = {}
        f = file(path, 'r')
        for i in f:
            r = Room(None)
            r.from_json(i)
            
            print r.name, r.exits
            
            level = r.coords[2]
            if self.levels.has_key(level):
                self.levels[level][r.vnum] = r
            else:
                self.levels[level] = {r.vnum: r, }

            self.rooms[r.vnum] = r
            z = self.get_or_create_zone(r.area, r.zone)
            self.zones[r.zone] = z
            z.update_room(r)
        for z in self.zones.values():
            z.update_exits()
            z.construct_boundary()
        f.close()
        
        

