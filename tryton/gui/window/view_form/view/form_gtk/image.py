# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gettext
import urllib.request

from gi.repository import Gdk, Gtk

from tryton.common import resize_pixbuf, data2pixbuf
from tryton.config import CONFIG
from .widget import Widget
from .binary import BinaryMixin

_ = gettext.gettext


class Image(BinaryMixin, Widget):

    def __init__(self, view, attrs):
        super(Image, self).__init__(view, attrs)

        self.height = int(attrs.get('height', 100))
        self.width = int(attrs.get('width', 300))

        self.widget = Gtk.Frame()
        self.widget.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.widget.get_accessible().set_name(attrs.get('string', ''))
        vbox = Gtk.VBox(spacing=3, margin=5)
        self.widget.add(vbox)
        self.event = Gtk.EventBox()
        self.event.drag_dest_set(Gtk.DestDefaults.ALL, [
            Gtk.TargetEntry.new('text/plain', 0, 0),
            Gtk.TargetEntry.new('text/uri-list', 0, 1),
            Gtk.TargetEntry.new("image/x-xpixmap", 0, 2)],
            Gdk.DragAction.MOVE)
        self.event.connect('drag_motion', self.drag_motion)
        self.event.connect('drag_data_received', self.drag_data_received)

        self.image = Gtk.Image()
        self.event.add(self.image)
        vbox.pack_start(self.event, expand=True, fill=True, padding=0)

        toolbar = self.toolbar()  # Set button attributes even if not display
        if not attrs.get('readonly'):
            toolbar.set_halign(Gtk.Align.CENTER)
            vbox.pack_start(
                toolbar, expand=False, fill=False, padding=0)

        self._readonly = False

    @property
    def filters(self):
        filters = super(Image, self).filters
        filter_image = Gtk.FileFilter()
        filter_image.set_name(_('Images'))
        for mime in ("image/png", "image/jpeg", "image/gif"):
            filter_image.add_mime_type(mime)
        for pat in ("*.png", "*.jpg", "*.gif", "*.tif", "*.xpm"):
            filter_image.add_pattern(pat)
        filters.insert(0, filter_image)
        return filters

    def _readonly_set(self, value):
        self._readonly = value
        self.but_select.set_sensitive(not value)
        self.but_clear.set_sensitive(not value)

    def clear(self, widget=None):
        super(Image, self).clear(widget=widget)
        self.update_img()

    def drag_motion(self, widget, context, x, y, timestamp):
        if self._readonly:
            return False
        context.drag_status(Gdk.DragAction.COPY, timestamp)
        return True

    def drag_data_received(self, widget, context, x, y, selection,
            info, timestamp):
        if self._readonly:
            return
        if info == 0:
            uri = selection.get_text().split('\n')[0]
            if uri:
                self.field.set_client(
                    self.record, urllib.request.urlopen(uri).read())
            self.update_img()
        elif info == 1:
            uri = selection.data.split('\r\n')[0]
            if uri:
                self.field.set_client(
                    self.record, urllib.request.urlopen(uri).read())
            self.update_img()
        elif info == 2:
            data = selection.get_pixbuf()
            if data:
                self.field.set_client(self.record, data)
                self.update_img()

    def update_img(self):
        value = None
        if self.field:
            value = self.field.get_client(self.record)
        if isinstance(value, int):
            if value > CONFIG['image.max_size']:
                value = False
            else:
                value = self.field.get_data(self.record)
        pixbuf = data2pixbuf(value)
        if pixbuf:
            pixbuf = resize_pixbuf(pixbuf, self.width, self.height)
        self.image.set_from_pixbuf(pixbuf)
        return bool(value)

    def display(self):
        super(Image, self).display()
        value = self.update_img()
        self.update_buttons(bool(value))
