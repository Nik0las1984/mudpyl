#coding: utf-8

import gtk
import numpy as np
import math
from numpy.linalg import norm
import cairo
from .map import *
from colors import *

TOWNS = [
    u'Вышгород',
    u'Город Владимир',
    u'Город Галич',
    u'Город Курск',
    u'Город Переяславль',
    u'Город Полоцк',
    u'Город Русса',
    u'Городище Корсунь',
    u'Господин Великий Новгород',
    u'град Любеч',
    u'град Путивль',
    u'Искоростень',
    u'Киев (новый город)',
    u'Меньск (Минск)',
    u'Муром',
    u'Псков',
    u'Ростов Великий',
    u'Рязань',
    u'Старая Ладога',
    u'Старая Ладога 2',
    u'Тверь',
    u'Торжок',
    u'Тотьма',
    u'Туров-град',
    u'Чернигов',
    ]

class MapLabel(gtk.Label):

    """Some info."""

    def __init__(self):
        gtk.Label.__init__(self)
        self.set_text('Some text')
        


class MapView(gtk.DrawingArea):
    def __init__(self, gui):
        gtk.DrawingArea.__init__(self)
        self.gui = gui
        self.gui.realm.mmap.gui = self
        self.mmap = self.gui.realm.mmap
        self.size = 10
        
        self.connect("expose-event", self.draw_map)
        self.connect('scroll_event', self.on_button_scroll_event)
        self.connect("button_press_event", self.button_press_event)
        self.connect("button_release_event", self.button_release_event)
        self.connect("motion_notify_event", self.motion_notify_event)
        
        self.set_events(gtk.gdk.EXPOSURE_MASK
                            | gtk.gdk.LEAVE_NOTIFY_MASK
                            | gtk.gdk.BUTTON_PRESS_MASK
                            | gtk.gdk.BUTTON_RELEASE_MASK
                            | gtk.gdk.POINTER_MOTION_MASK
                            | gtk.gdk.POINTER_MOTION_HINT_MASK)
        
        self.ofs = np.int_([300, 300])
        
        self.move_flag = False
        self.move_coord = None
        
        self.move_room_flag = False
        self.move_room_coord = None
        self.mode_room_room = None
        
        self.gcs = {}
        
        self.active = None
        self.active_zone = None
        self.selected = []
        
        self.bound_rooms = None

        self.rmenu = self.room_menu()
        
        
        
        self.map_label = MapLabel()
        
        
        # меню вверху
        self.zone_combobox = gtk.combo_box_new_text()
        self.zone_index = {}
        self.create_list_zones()
        self.zone_combobox.connect('changed', self.zone_combobox_changed)
        
        self.map_detalization = gtk.combo_box_new_text()
        self.detalization = 1
        self.create_map_detalization()
        self.map_detalization.connect('changed', self.map_detalization_changed)
        

    
    def create_map_detalization(self):
        self.map_detalization.append_text(u'Детализация отрисовки:')
        self.map_detalization.append_text(u'Текущая зона')
        self.map_detalization.append_text(u'Текущая зона+граничные')
        self.map_detalization.append_text(u'Все зоны')
        self.map_detalization.append_text(u'Приграничные комнаты+BBox')
        self.map_detalization.append_text(u'Приграничные комнаты+Центр зоны')
        self.map_detalization.set_active(1)
    
    def map_detalization_changed(self, combobox):
        index = combobox.get_active()
        if index:
            self.detalization = index
            self.queue_draw()
        return
    
    def create_list_zones(self):
        self.zone_combobox.get_model().clear()
        self.zone_index = {}
        
        self.zone_combobox.append_text(u'Список зон:')
        self.zone_combobox.set_active(0)
        ind = 0
        for z in self.mmap.zones.values():
            if z.name:
                self.zone_combobox.append_text(z.name)
                ind += 1
                self.zone_index[z.name] = (z, ind)
    
    def update_list_zones(self):
        try:
            ind = self.zone_index[self.mmap.zones[self.active.zone].name][1]
            self.zone_combobox.set_active(ind)
        except:
            self.zone_combobox.set_active(0)
        
    
    def zone_combobox_changed(self, combobox):
        model = combobox.get_model()
        index = combobox.get_active()
        if index:
            self.active_zone = self.zone_index[unicode(model[index][0])][0]
            self.center_to_room(self.active_zone.rooms.values()[0])
            self.queue_draw()
        return

    
    def create_gcs(self):
        for i in COLORS.keys():
            self.gcs[i] = self.get_colormap().alloc_color(COLORS[i], True, True)
        
        c = self.get_colormap().alloc_color('#3366ff', True, True)
        self.gcs['active'] = c
        
        c = self.get_colormap().alloc_color('#0000cc', True, True)
        self.gcs['zone'] = c

        c = self.get_colormap().alloc_color('#808080', True, True)
        self.gcs['def'] = c
        
        c = self.get_colormap().alloc_color('#111111', True, True)
        self.gcs['def_stoke'] = c
        
        c = self.get_colormap().alloc_color('#000000', True, True)
        self.gcs['dt'] = c
        
        c = self.get_colormap().alloc_color('#ff0000', True, True)
        self.gcs['slow_dt'] = c



    
    def motion_notify_event(self, widget, event):
        #self.gui.realm.info('right %s ' % self.mouse_to_coord(np.int_([event.x, event.y])))
        if event.is_hint and self.move_flag:
            d = np.int_([event.x, event.y])
            self.ofs += d - self.move_coord
            self.move_coord = d
        
        if event.is_hint and self.move_room_flag:
            d = self.mouse_to_coord(np.int_([event.x, event.y]))
            dd = d - self.move_room_coord
            for r in self.selected:
                if r:
                    r.move(np.int_([dd[0], dd[1], 0]))
            self.move_room_coord = d
        
        self.queue_draw()
        return True
    
    def mouse_to_coord(self, mc):
        return self.w2m(mc)
    
    def w2m(self, mc):
        h = self.h()
        c = mc - self.ofs + np.int_([h, -h])
        c[0] /=  h * 2
        c[1] /= -h * 2
        return c
    
    def m2w(self, c):
        h = self.h()
        nc = np.int_([c[0], c[1]])
        nc[0] *=  h * 2
        nc[1] *= -h * 2
        return nc + self.ofs
    
    def check_coords(self, c):
        x_size, y_size = self.window.get_size()
        return x_size > c[0] and c[0] > 0 and y_size > c[1] and c[1] > 0
    
    def button_press_event(self, widget, event):
        if event.button == 3:
            c = self.mouse_to_coord(np.int_([event.x, event.y]))
            
            for r in self.selected:
                if r and r.coords[0] == c[0] and r.coords[1] == c[1]:
                    self.rmenu.popup(None,None,None,event.button,event.time)
                    return True
            
            self.move_flag = True
            self.move_coord = np.int_([event.x, event.y])
            
        if event.button == 1:
            #self.gui.realm.info('right %s ' % self.mouse_to_coord(np.int_([event.x, event.y])))
            self.move_room_coord = self.mouse_to_coord(np.int_([event.x, event.y]))
            r = self.mmap.get_by_coords(self.move_room_coord, self.active_zone.vnum)

            # Если кликнули по выделенной, то можем тащить
            if r in self.selected:
                
                self.move_room_flag = True
            else:
                # Выделение мышкой
                if event.get_state() & gtk.gdk.CONTROL_MASK:
                    self.selected.append(r)
                else:
                    self.selected = [r,]
            
            # Если выделена и двойной клик, то выделяем все в зоне
            if event.type == gtk.gdk._2BUTTON_PRESS:
                if r in self.selected:
                    self.selected = []
                    z = self.mmap.zones[r.zone]
                    for r1 in z.rooms.values():
                        self.selected.append(r1)
                        for ri in r1.exits.values():
                            r2 = self.mmap.rooms[ri]
                            if not r2.parsed_flag and r2 not in self.selected:
                                self.selected.append(r2)
                    
            
            self.queue_draw()
    
    def rmenu_response(self, widget, s):
        if s == u'dt':
            for r in self.selected:
                r.toggle_dt()
        if s == u'sdt':
            for r in self.selected:
                r.toggle_slow_dt()
        if s == u'yama':
            for r in self.selected:
                r.toggle_yama()
        if s == u'level+':
            for r in self.selected:
                r.move(np.int_([0,0,1]))
        if s == u'level-':
            for r in self.selected:
                r.move(np.int_([0,0,-1]))
        
        if s == u'active_zone':
            if len(self.selected) > 0:
                r = self.selected[0]
                self.active_zone = self.mmap.zones[r.zone]
        self.queue_draw()
            
    def button_release_event(self, widget, event):
        if event.button == 3:
            self.move_flag = False
        if event.button == 1:
            self.move_room_flag = False
    
    # Мышка
    def on_button_scroll_event(self, button, event):
        d = int(self.size * 0.1)
        if d < 1:
            d = 1
        if event.direction == gtk.gdk.SCROLL_UP:
            self.size += d
        if event.direction == gtk.gdk.SCROLL_DOWN:
            self.size -= d
        if self.size > 100:
            self.size = 100
        if self.size < 1:
            self.size = 1
        self.queue_draw()
        return True
    
    def get_gc(self):
        return self.get_style().fg_gc[gtk.STATE_NORMAL]
    
    def h(self):
        return self.size
    
    def rc(self, r):
        return self.m2w(r.coords) - np.int_([self.h() / 2, self.h() / 2])
    
    def draw_room(self, r, active, current_level, cr, draw_room = True):
        
        gc = self.gcs['def']
        if self.gcs.has_key(r.terrain):
            gc = self.gcs[r.terrain]
        
        if r.slow_dt_flag:
            gc = self.gcs['slow_dt']
        
        if r.dt_flag:
            gc = self.gcs['dt']
        
        
        h = self.h()
        x, y = self.rc(r)
        
        x += r.coords[2] * h / 3
        y -= r.coords[2] * h / 3
        
        
        if draw_room:
            if current_level:
                cr.set_source_color(gc)
            else:
                cr.set_source_rgba(0.5, 0.5, 0.5, 0.4)
            cr.rectangle(x, y, h, h)
            cr.fill()
            #self.window.draw_rectangle(gc, gtk.TRUE, x, y, h, h)
            #self.window.draw_rectangle(self.get_gc(), gtk.FALSE, x, y, h, h)
            cr.set_line_width(1)
            
            if h > 5:
                if current_level:
                    cr.set_source_color(self.gcs['def_stoke'])
                else:
                    cr.set_source_rgba(0, 0, 0, 0.4)
                cr.rectangle(x, y, h, h)
                cr.stroke()
        
        #if r.name:
        #    cr.move_to(x, y + h/2)
        #    cr.show_text(r.name)

        for e in r.exits.keys():
            ngb = self.mmap.rooms[r.exits[e]]
            
            d = norm(ngb.coords - r.coords)
            if h < 3 and d < 10:
                continue
            
            w = DIRS_PLUS[e] * h / 2
            x1 = x + w[0] + h / 2
            y1 = y - w[1] + h / 2
                
            cr.move_to(x1, y1)
            cr.line_to(x1 + w[0], y1 - w[1])
            
            c = self.rc(ngb)
            x2, y2 = c[0], c[1]
            x2 += r.coords[2] * h / 3 - w[0] + h / 2
            y2 -= r.coords[2] * h / 3 - w[1] - h / 2
                
            #cr.line_to(x2 - w[0], y2 + w[1])
            w1 = DIRS_PLUS[e] * np.int_([abs(x2-x1), abs(y2-y1), 0])
            #cr.curve_to(x1 + 2 * w[0], y1 - 2 * w[1], x2 - 2 * w[0], y2 + 2 * w[1], x2 - w[0], y2 + w[1])
            cr.curve_to(x1 + w[0] + w1[0]/2, y1  - w[1] - w1[1]/2,
                        x2 - w[0] - w1[0]/2, y2 + w[1] + w1[1]/2,
                        x2 - w[0], y2 + w[1])
            cr.stroke()
           
            #self.window.draw_line(self.get_gc(), x1, y1, x1 + w[0], y1 - w[1])
        
        if draw_room:
            cr.set_line_width(2)
            if active:
                cr.set_source_color(self.gcs['active'])
                cr.rectangle(x-2, y-2, h+4, h+4)
                cr.stroke()
            
            if r in self.selected:
                cr.set_source_rgba(1, 0, 0, 1)
                cr.rectangle(x-2, y-2, h+4, h+4)
                cr.stroke()
        
    
    def draw_map(self, drawingarea, event):
        cr = self.window.cairo_create()
        
        #for z in self.gui.realm.mmap.zones.keys():
        #    if z:
        #        self.draw_zone(self.gui.realm.mmap.zones[z], cr)

        
        if self.detalization in [1, 2]:
            if self.active_zone:
                
                # Рисуем текущую зону
                self.draw_zone(self.active_zone, cr)
                
                # Если детализация 2
                if self.detalization == 2:
                    for z1 in self.active_zone.exits.values():
                        self.draw_zone(z1, cr)
        
        if self.detalization == 3:
            # Рисуем все зоны
            for z in self.mmap.zones.values():
                self.draw_zone(z, cr)
        
        # Рисуем ббоксы
        if self.detalization == 4:
            for z in self.mmap.zones.values():
                self.draw_bbox(z, cr)
            self.draw_bound_rooms(cr)
        
        # Рисуем центра
        if self.detalization == 5:
            for z in self.mmap.zones.values():
                if z.name:
                    self.draw_zone_center(z, cr)
            #self.draw_bound_rooms(cr, True)
        
        """
        if self.active:
            
            z = self.mmap.zones[self.active.zone]
            self.draw_zone(z, cr)
            for z1 in z.exits.values():
                self.draw_zone(z1, cr)
       """     
            #for z1 in self.mmap.zones.values():
            #    self.draw_zone(z1, cr)
        
        """
        for l in self.mmap.levels.keys():
            for r in self.mmap.levels[l]:
                room = self.gui.realm.mmap.rooms[r]
                ral = 0
                if self.active:
                    ral = self.active.coords[2]
                    
                    z = self.mmap.zones[self.active.zone]
                    
                    if z.check_room(room) or z.check_not_parsed_room(room) or z.check_zone_vnum(room.zone):
                        self.draw_room(room, room == self.active, room.coords[2] == ral, cr)
        """
        """
        for r in self.gui.realm.mmap.rooms.keys():
            room = self.gui.realm.mmap.rooms[r]
            ral = 0
            if self.active:
                ral = self.gui.realm.mmap.rooms[self.active].coords[2]
            self.draw_room(room, r == self.active, room.coords[2] == ral, cr)
        """
        #
    
    def draw_zone_name(self, z, cr):
        h = self.h()
        # Координаты
        c = self.m2w(np.int_([(z.bmin[0] + z.bmax[0]) / 2, z.bmax[1]]))
            
        cr.select_font_face("terminus", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(max(h, 12) + 2)

        (x, y, width, height, dx, dy) = cr.text_extents(z.name)
        cr.move_to(c[0]- width/2, c[1] - h)
        cr.show_text(z.name)
    
    def draw_bbox(self, z, cr):
        x1 = self.m2w(z.bmin)
        x2 = self.m2w(z.bmax)
        cr.set_source_rgba(0, 0, 1, 1)
        cr.rectangle(x1[0], x1[1], x2[0]-x1[0], x2[1]-x1[1])
        cr.stroke()
        
        # Рисуем название
        if z.name:
            self.draw_zone_name(z, cr)
    
    def draw_zone_center(self, z, cr):
        h = self.h()
        c = self.m2w(z.get_avg())
        if z.name in TOWNS:
            cr.set_source_rgba(1, 0, 0, 1)
            cr.arc(c[0], c[1], h*6, 0, 2*math.pi)
            self.draw_zone_name(z, cr)
        else:
            cr.set_source_rgba(0, 0, 1, 1)
            cr.arc(c[0], c[1], h*3, 0, 2*math.pi)
        
        cr.fill()
        # Рисуем линки
        for z1 in z.exits.values():
            if z1.name:
                c1 = self.m2w(z1.get_avg())
                cr.move_to(c[0], c[1])
                cr.line_to(c1[0], c1[1])
                cr.stroke()
        
        # Рисуем название
        if z.name and h > 5:
            self.draw_zone_name(z, cr)
    
    def draw_bound_rooms(self, cr, only_links = False):
        if not self.bound_rooms:
            self.bound_rooms = []
            for r in self.mmap.rooms.values():
                if r.bound_flag:
                    self.bound_rooms.append(r)
        for r in self.bound_rooms:
            self.draw_room(r, r == self.active, r.coords[2] == self.active.coords[2], cr, not only_links)

    
    def draw_zone(self, z, cr):
        """
        cr.set_source_rgba(0, 0, 1, 0.1)
        h = self.h()
        
        for x in z.mmy.keys():
            y1 = z.mmy[x][0]
            y2 = z.mmy[x][1]
            d = y2 - y1
            x1 = x * h * 2 + self.ofs[0] - h
            y1 = -y1 * h * 2 + self.ofs[1] + h
            cr.rectangle(x1, y1, 2 * h, - d * h * 2 - 2 * h)
            cr.fill()
        for y in z.mmx.keys():
            x1 = z.mmx[y][0]
            x2 = z.mmx[y][1]
            d = x2 - x1
            x1 = x1 * h * 2 + self.ofs[0] - h
            y1 = -y * h * 2 + self.ofs[1] + h
            cr.rectangle(x1, y1, d * h * 2 + 2 * h, -2 * h)
            cr.fill()
        """
        """
        if z.name:
            cr.set_source_rgba(0, 0, 1, 1)
            cr.move_to(z.get_avgx() * 2 * h + self.ofs[0], - z.get_maxy() * h * 2 - h/2 + self.ofs[1])
            cr.show_text(z.name)
        """
        
        """
        x1 = self.m2w(z.bmin)
        x2 = self.m2w(z.bmax)
        cr.set_source_rgba(0, 0, 1, 1)
        cr.rectangle(x1[0], x1[1], x2[0]-x1[0], x2[1]-x1[1])
        cr.stroke()
        """
        
        # Рисуем название
        h = self.h()
        if z.name and h > 5:
            self.draw_zone_name(z, cr)
        
        # Если зона одна, рисуем название выходов
        if self.detalization == 1 and h > 5:
            already = []
            for e in z.exits.keys():
                r = self.mmap.rooms[e]
                rc = None
                d = None
                for e1 in r.exits.keys():
                    r1 = self.mmap.rooms[r.exits[e1]]
                    if r1.zone != r.zone and r1.area:
                        d = e1
                        rc = r1
                        break
                if rc and rc.zone not in already:
                    already.append(rc.zone)
                    c = self.m2w(r.coords + DIRS_PLUS[d])
                    cr.select_font_face("terminus", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                    cr.set_font_size(max(h, 12))
                    (x, y, width, height, dx, dy) = cr.text_extents(r1.area)
                    
                    if d == 'e':
                        cr.move_to(c[0], c[1])
                    elif d == 'w':
                        cr.move_to(c[0]-width, c[1])
                    else:
                        cr.move_to(c[0]-width/2, c[1])
                    cr.show_text(r1.area)
        
        if z.name and False:
            cr.set_source_rgba(0, 0, 1, 1)
            first = False
            for c in z.boundary:
                cw = self.m2w(c)
                if first:
                    cr.move_to(cw[0], cw[1])
                    first = False
                else:
                    cr.line_to(cw[0], cw[1])
            
            if len(z.boundary) > 0:
                cw = self.m2w(z.boundary[0])
                cr.line_to(cw[0], cw[1])
            cr.stroke()
        
        
        for r in z.rooms.values():
            if self.check_coords(self.m2w(r.coords)):
                self.draw_room(r, r == self.active, r.coords[2] == self.active.coords[2], cr)

                for ri in r.exits.values():
                    r1 = self.mmap.rooms[ri]
                    if not r1.parsed_flag:
                        self.draw_room(r1, False, r1.coords[2] == self.active.coords[2], cr)
            
    
    def update(self, room):
        self.active = room
        self.active_zone = self.mmap.zones[self.active.zone]
        
        self.center_to_room(room)
        
        self.queue_draw()
        
        # обновляем инфу внизу
        self.update_mal_label()
        
        # обновляем комбобокс с зонами
        self.update_list_zones()
    
    def center_to_room(self, room):
        c = self.rc(room)
        r = self.get_allocation()
        #print r
        self.ofs += np.int_([r.width / 2, r.height / 2]) - c
    
    def update_mal_label(self):
        if self.active:
            s = 'Zone: %s, Room: %s, Terrain: %s' % (self.active.area, self.active.name, self.active.terrain)
        else:
            s = 'No active room'
        self.map_label.set_text(s)
    
    def get_widget(self):
        
        box1 = gtk.HBox()
        box1.pack_start(self.zone_combobox)
        box1.pack_start(self.map_detalization)
        
        box = gtk.VBox()
        box.pack_start(box1, expand = False)
        box.pack_start(self)
        box.pack_end(self.map_label, expand = False)
        return box
    
    def room_menu(self):
        menu = gtk.Menu()
        menu1 = gtk.MenuItem(u'ДТ')
        menu.append(menu1)
        menu1.connect("activate", self.rmenu_response, u'dt')
        
        menu1 = gtk.MenuItem(u'Слоу ДТ')
        menu.append(menu1)
        menu1.connect("activate", self.rmenu_response, u'sdt')
        
        menu1 = gtk.MenuItem(u'Яма')
        menu.append(menu1)
        menu1.connect("activate", self.rmenu_response, u'yama')
        
        menu1 = gtk.MenuItem(u'Уровень +')
        menu.append(menu1)
        menu1.connect("activate", self.rmenu_response, u'level+')
        
        menu1 = gtk.MenuItem(u'Уровень -')
        menu.append(menu1)
        menu1.connect("activate", self.rmenu_response, u'level-')
        
        menu1 = gtk.MenuItem(u'Активная зона')
        menu.append(menu1)
        menu1.connect("activate", self.rmenu_response, u'active_zone')
        
        

        menu.show_all()
        return menu
    
        