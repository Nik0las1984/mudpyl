import cairo

import gtk as Gtk
from gtk import gdk as Gdk
from gtk.gdk import Pixbuf as GdkPixbuf
from gtk import Object as GObject

import sys

def _surface_from_file(file_location, ctx):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(file_location)
    surface = ctx.get_target().create_similar(
        cairo.CONTENT_COLOR_ALPHA, pixbuf.get_width(),
        pixbuf.get_height())

    ctx_surface = cairo.Context(surface)
    Gdk.cairo_set_source_pixbuf(ctx_surface, pixbuf, 0, 0)
    ctx_surface.paint()
    return surface

class ImageViewer(Gtk.DrawingArea, Gtk.Scrollable):
    __gtype_name__ = 'ImageViewer'

    __gproperties__ = {
        "hscroll-policy": (Gtk.ScrollablePolicy, "hscroll-policy",
                           "hscroll-policy", Gtk.ScrollablePolicy.MINIMUM,
                           GObject.PARAM_READWRITE),
        "hadjustment": (Gtk.Adjustment, "hadjustment", "hadjustment",
                        GObject.PARAM_READWRITE),
        "vscroll-policy": (Gtk.ScrollablePolicy, "hscroll-policy",
                           "hscroll-policy", Gtk.ScrollablePolicy.MINIMUM,
                           GObject.PARAM_READWRITE),
        "vadjustment": (Gtk.Adjustment, "hadjustment", "hadjustment",
                        GObject.PARAM_READWRITE),
    }
    def __init__(self, zoom):
        Gtk.DrawingArea.__init__(self)

        self._file_location = None
        self._surface = None
        self._zoom = zoom
        self._offset = None

        self._hadj = None
        self._vadj = None

        self.connect('draw', self.__draw_cb)

    def set_file_location(self, file_location):
        self._file_location = file_location
        self.queue_draw()

    def do_get_property(self, prop):
        pass

    def do_set_property(self, prop, value):
        if prop.name == 'hadjustment':
            if value is not None:
                hadj = value
                hadj.connect('value-changed', self.__hadj_value_changed_cb)
                self._hadj = hadj

        elif prop.name == 'vadjustment':
            if value is not None:
                vadj = value
                vadj.connect('value-changed', self.__vadj_value_changed_cb)
                self._vadj = vadj

    def _update_adjustments(self):
        alloc = self.get_allocation()
        scaled_width = self._surface.get_width() * self._zoom
        scaled_height = self._surface.get_height() * self._zoom

        page_size_x = alloc.width * 1.0 / scaled_width
        self._hadj.set_lower(0)
        self._hadj.set_page_size(page_size_x)
        self._hadj.set_upper(1.0)
        self._hadj.set_step_increment(0.1)
        self._hadj.set_page_increment(0.5)

        page_size_y = alloc.height * 1.0 / scaled_height
        self._vadj.set_lower(0)
        self._vadj.set_page_size(page_size_y)
        self._vadj.set_upper(1.0)
        self._vadj.set_step_increment(0.1)
        self._vadj.set_page_increment(0.5)

    def __hadj_value_changed_cb(self, adj):
        alloc = self.get_allocation()
        scaled_width = self._surface.get_width() * self._zoom
        max_offset_x = scaled_width - alloc.width
        max_value = self._hadj.get_upper() - self._hadj.get_page_size()
        value = adj.get_value()

        offset_x = -1 * value * max_offset_x / max_value

        self._offset = (offset_x, self._offset[1])
        self.queue_draw()

    def __vadj_value_changed_cb(self, adj):
        alloc = self.get_allocation()
        scaled_height = self._surface.get_height() * self._zoom
        max_offset_y = scaled_height - alloc.height
        max_value = self._hadj.get_upper() - self._hadj.get_page_size()
        value = adj.get_value()

        offset_y = -1 * value * max_offset_y / max_value

        self._offset = (self._offset[0], offset_y)
        self.queue_draw()

    def __draw_cb(self, widget, ctx):
        if self._surface is None:
            if self._file_location is None:
                return
            self._surface = _surface_from_file(self._file_location, ctx)
            self._update_adjustments()

        if self._offset is None:
            self._offset = (0, 0)

        ctx.translate(*self._offset)
        ctx.scale(self._zoom, self._zoom)
        ctx.set_source_surface(self._surface, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_NEAREST)
        ctx.paint()


window = Gtk.Window()
window.set_size_request(800, 600)
window.connect("destroy", Gtk.main_quit)
window.show()

scrolled_window = Gtk.ScrolledWindow()
scrolled_window.set_policy(Gtk.PolicyType.ALWAYS,
                           Gtk.PolicyType.ALWAYS)

#scrolled_window.set_kinetic_scrolling(False)
window.add(scrolled_window)
scrolled_window.show()

file_location = sys.argv[1]
zoom = float(sys.argv[2])

view = ImageViewer(zoom)
view.set_file_location(file_location)
scrolled_window.add(view)
view.show()

Gtk.main()
