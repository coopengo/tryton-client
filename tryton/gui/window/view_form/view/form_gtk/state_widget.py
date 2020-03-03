# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import logging

from gi.repository import Gtk, Pango

import tryton.common as common

logger = logging.getLogger(__name__)


class StateMixin(object):

    def __init__(self, *args, **kwargs):
        self.attrs = kwargs.pop('attrs')
        super(StateMixin, self).__init__(*args, **kwargs)

    def state_set(self, record):
        if record:
            state_changes = record.expr_eval(self.attrs.get('states', {}))
        else:
            state_changes = {}
        if state_changes.get('invisible', self.attrs.get('invisible')):
            self.hide()
        else:
            self.show()


class Label(StateMixin, Gtk.Label):

    def state_set(self, record):
        super(Label, self).state_set(record)
        if 'name' in self.attrs and record:
            field = record.group.fields[self.attrs['name']]
        else:
            field = None
        if not self.attrs.get('string', True) and field:
            if record:
                text = field.get_client(record) or ''
            else:
                text = ''
            self.set_text(text)
        if record:
            state_changes = record.expr_eval(self.attrs.get('states', {}))
        else:
            state_changes = {}
        required = ((field and field.attrs.get('required'))
                or state_changes.get('required'))
        readonly = ((field and field.attrs.get('readonly'))
                or state_changes.get('readonly', not bool(field)))
        common.apply_label_attributes(self, readonly, required)
        if field:
            self._format_set(record, field)

    def _set_background(self, value, attrlist):
        if value not in common.COLOR_RGB:
            logger.info('This color is not supported => %s', value)
        color = common.COLOR_RGB.get(value, common.COLOR_RGB['black'])
        if hasattr(Pango, 'AttrBackground'):
            attrlist.change(Pango.AttrBackground(
                    color[0], color[1], color[2], 0, -1))

    def _set_foreground(self, value, attrlist):
        if value not in common.COLOR_RGB:
            logger.info('This color is not supported => %s', value)
        color = common.COLOR_RGB.get(value, common.COLOR_RGB['black'])
        if hasattr(Pango, 'AttrForeground'):
            attrlist.change(Pango.AttrForeground(
                    color[0], color[1], color[2], 0, -1))

    def _set_font(self, value, attrlist):
        attrlist.change(Pango.AttrFontDesc(
                Pango.FontDescription(value), 0, -1))

    def _format_set(self, record, field):
        attrlist = Pango.AttrList()
        functions = {
            'color': self._set_foreground,
            'fg': self._set_foreground,
            'bg': self._set_background,
            'font': self._set_font
            }
        attrs = record.expr_eval(field.get_state_attrs(record).
            get('states', {}))
        states = record.expr_eval(self.attrs.get('states', {})).copy()
        states.update(attrs)

        for attr in list(states.keys()):
            if not states[attr]:
                continue
            key = attr.split('_')
            if key[0] == 'field':
                continue
            if key[0] == 'label':
                key = key[1:]
            if isinstance(states[attr], str):
                key.append(states[attr])
            if key[0] in functions:
                if len(key) != 2:
                    raise ValueError(common.FORMAT_ERROR + attr)
                functions[key[0]](key[1], attrlist)
        self.set_attributes(attrlist)


class VBox(StateMixin, Gtk.VBox):
    pass


class Image(StateMixin, Gtk.Image):

    def state_set(self, record):
        super(Image, self).state_set(record)
        if not record:
            return
        name = self.attrs['name']
        if name in record.group.fields:
            field = record.group.fields[name]
            name = field.get(record)
        self.set_from_pixbuf(common.IconFactory.get_pixbuf(
                name, int(self.attrs.get('size', 48))))


class Frame(StateMixin, Gtk.Frame):

    def __init__(self, label=None, attrs=None):
        if not label:  # label must be None to have no label widget
            label = None
        super(Frame, self).__init__(label=label, attrs=attrs)
        if not label:
            self.set_shadow_type(Gtk.ShadowType.NONE)
        self.set_border_width(0)


class ScrolledWindow(StateMixin, Gtk.ScrolledWindow):

    def state_set(self, record):
        # Force to show first to ensure it is displayed in the Notebook
        self.show()
        super(ScrolledWindow, self).state_set(record)


class Notebook(StateMixin, Gtk.Notebook):

    def state_set(self, record):
        super(Notebook, self).state_set(record)
        if record:
            state_changes = record.expr_eval(self.attrs.get('states', {}))
        else:
            state_changes = {}
        if state_changes.get('readonly', self.attrs.get('readonly')):
            for widgets in self.widgets.values():
                for widget in widgets:
                    widget._readonly_set(True)


class Expander(StateMixin, Gtk.Expander):

    def __init__(self, label=None, attrs=None):
        if not label:
            label = None
        super(Expander, self).__init__(label=label, attrs=attrs)
