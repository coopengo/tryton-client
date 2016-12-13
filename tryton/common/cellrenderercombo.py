# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gtk
import gobject

from tryton.common.selection import selection_shortcuts


class CellRendererCombo(gtk.CellRendererCombo):

    def set_sensitive(self, value):
        self.set_property('sensitive', value)

    def do_activate(self, event, widget, path, background_area, cell_area,
            flags):
        if not self.props.visible:
            return
        return gtk.CellRendererCombo.do_activate(self, event, widget, path,
            background_area, cell_area, flags)

    def do_start_editing(self, event, widget, path, background_area,
            cell_area, flags):
        if not self.props.visible:
            return
        if not event:
            if hasattr(gtk.gdk.Event, 'new'):
                event = gtk.gdk.Event.new(gtk.gdk.KEY_PRESS)
            else:
                event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        editable = gtk.CellRendererCombo.do_start_editing(self, event, widget,
            path, background_area, cell_area, flags)

        colormap = editable.get_colormap()
        style = editable.get_style()
        if hasattr(self, 'background') \
                and getattr(self, 'background') != 'white':
            bg_color = colormap.alloc_color(getattr(self, 'background'))
            fg_color = gtk.gdk.color_parse("black")
            editable.modify_bg(gtk.STATE_ACTIVE, bg_color)
            editable.modify_base(gtk.STATE_NORMAL, bg_color)
            editable.modify_fg(gtk.STATE_NORMAL, fg_color)
            editable.modify_text(gtk.STATE_NORMAL, fg_color)
            editable.modify_text(gtk.STATE_INSENSITIVE, fg_color)
        else:
            editable.modify_bg(gtk.STATE_ACTIVE, style.bg[gtk.STATE_ACTIVE])
            editable.modify_base(gtk.STATE_NORMAL,
                style.base[gtk.STATE_NORMAL])
            editable.modify_fg(gtk.STATE_NORMAL, style.fg[gtk.STATE_NORMAL])
            editable.modify_text(gtk.STATE_NORMAL,
                style.text[gtk.STATE_NORMAL])
            editable.modify_text(gtk.STATE_INSENSITIVE,
                style.text[gtk.STATE_INSENSITIVE])
        return selection_shortcuts(editable)

gobject.type_register(CellRendererCombo)
