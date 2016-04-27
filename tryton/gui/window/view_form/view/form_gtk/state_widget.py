# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gtk
import pango
import logging

from tryton.common import COLOR_RGB, FORMAT_ERROR


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


class Label(StateMixin, gtk.Label):

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
        if ((field and field.attrs.get('required'))
                or state_changes.get('required')):
            weight = pango.WEIGHT_BOLD
        else:
            weight = pango.WEIGHT_NORMAL
        if ((field and field.attrs.get('readonly'))
                or state_changes.get('readonly')):
            style = pango.STYLE_NORMAL
            weight = pango.WEIGHT_NORMAL
        else:
            style = pango.STYLE_ITALIC
        attrlist = pango.AttrList()
        attrlist.change(pango.AttrWeight(weight, 0, -1))
        attrlist.change(pango.AttrStyle(style, 0, -1))
        if field is not None:
            self._format_set(record, field, attrlist)
        self.set_attributes(attrlist)

    def _set_background(self, value, attrlist):
        if value not in COLOR_RGB:
            logging.getLogger(__name__).info('This color is not supported' +
                '=> %s' % value)
        color = COLOR_RGB.get(value, COLOR_RGB['black'])
        attrlist.change(pango.AttrBackground(color[0], color[1],
                color[2], 0, -1))

    def _set_foreground(self, value, attrlist):
        if value not in COLOR_RGB:
            logging.getLogger(__name__).info('This color is not supported' +
                '=> %s' % value)
        color = COLOR_RGB.get(value, COLOR_RGB['black'])
        attrlist.change(pango.AttrForeground(color[0], color[1],
                color[2], 0, -1))

    def _set_font(self, value, attrlist):
        attrlist.change(pango.AttrFontDesc(pango.FontDescription(value),
                0, -1))

    def _format_set(self, record, field, attrlist):
        functions = {
            'color': self._set_foreground,
            'fg': self._set_foreground,
            'bg': self._set_background,
            'font': self._set_font
            }
        if getattr(self.attrs, 'states', None):
            attrs = record.expr_eval(field.get_state_attrs(record)['states'])
            states = record.expr_eval(self.attrs['states']).copy()
            states.update(attrs)
        else:
            states = record.expr_eval(field.get_state_attrs(record)['states'])
        for attr in states.keys():
            if not states[attr]:
                continue
            key = attr.split('_')
            if key[0] == 'field':
                continue
            if key[0] == 'label':
                key = key[1:]
            if key[0] in functions:
                if len(key) != 2:
                    raise ValueError(FORMAT_ERROR + attr)
                functions[key[0]](key[1], attrlist)


class VBox(StateMixin, gtk.VBox):
    pass


class Image(StateMixin, gtk.Image):
    pass


class Frame(StateMixin, gtk.Frame):

    def __init__(self, label=None, attrs=None):
        if not label:  # label must be None to have no label widget
            label = None
        super(Frame, self).__init__(label=label, attrs=attrs)
        if not label:
            self.set_shadow_type(gtk.SHADOW_NONE)
        self.set_border_width(0)


class ScrolledWindow(StateMixin, gtk.ScrolledWindow):
    pass


class Notebook(StateMixin, gtk.Notebook):

    def state_set(self, record):
        super(Notebook, self).state_set(record)
        if record:
            state_changes = record.expr_eval(self.attrs.get('states', {}))
        else:
            state_changes = {}
        if state_changes.get('readonly', self.attrs.get('readonly')):
            for widgets in self.widgets.itervalues():
                for widget in widgets:
                    widget._readonly_set(True)


class Alignment(gtk.Alignment):

    def __init__(self, widget, attrs):
        super(Alignment, self).__init__(
            float(attrs.get('xalign', 0.0)),
            float(attrs.get('yalign', 0.5)),
            float(attrs.get('xexpand', 1.0)),
            float(attrs.get('yexpand', 1.0)))
        self.add(widget)
        widget.connect('show', lambda *a: self.show())
        widget.connect('hide', lambda *a: self.hide())
