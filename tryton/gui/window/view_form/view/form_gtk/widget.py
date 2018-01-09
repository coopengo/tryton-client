# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gtk
import gobject
import gettext
import pango

from tryton.common import COLORS
import tryton.common as common
from tryton.gui.window.nomodal import NoModal
from tryton.common import TRYTON_ICON
from tryton.common import RPCExecute, RPCException
from tryton.common import FORMAT_ERROR
from tryton.common.widget_style import widget_class

_ = gettext.gettext


class Widget(object):
    expand = False

    def __init__(self, view, attrs):
        super(Widget, self).__init__()
        self.view = view
        self.attrs = attrs
        self.widget = None
        self.mnemonic_widget = None
        self.colors = {}
        self.visible = True
        self.color_name = None
        self._readonly = False

    @property
    def field_name(self):
        return self.attrs['name']

    @property
    def model_name(self):
        return self.view.screen.model_name

    @property
    def record(self):
        return self.view.screen.current_record

    @property
    def field(self):
        if self.record:
            return self.record.group.fields[self.field_name]

    def destroy(self):
        pass

    def sig_activate(self, widget=None):
        # emulate a focus_out so that the onchange is called if needed
        self._focus_out()

    def _readonly_set(self, readonly):
        self._readonly = readonly

    def _required_set(self, required):
        pass

    def _color_widget(self):
        return self.widget

    def _invisible_widget(self):
        return self.widget

    @property
    def modified(self):
        return False

    def send_modified(self, *args):
        def send(value):
            if not self.widget.props.window:
                return
            if self.record and self.get_value() == value:
                self.record.signal('record-modified')

        def get_value():
            if not self.widget.props.window:
                return
            gobject.timeout_add(300, send, self.get_value())
        # Wait the current event is finished to retreive the value
        gobject.idle_add(get_value)
        return False

    def color_set(self, name):
        self.color_name = name
        widget = self._color_widget()

        if not self.colors:
            style = widget.get_style()
            self.colors = {
                'bg_color_active': style.bg[gtk.STATE_ACTIVE],
                'bg_color_insensitive': style.bg[gtk.STATE_INSENSITIVE],
                'base_color_normal': style.base[gtk.STATE_NORMAL],
                'base_color_insensitive': style.base[gtk.STATE_INSENSITIVE],
                'fg_color_normal': style.fg[gtk.STATE_NORMAL],
                'fg_color_insensitive': style.fg[gtk.STATE_INSENSITIVE],
                'text_color_normal': style.text[gtk.STATE_NORMAL],
                'text_color_insensitive': style.text[gtk.STATE_INSENSITIVE],
            }

        if COLORS.get(name):
            colormap = widget.get_colormap()
            bg_color = colormap.alloc_color(COLORS.get(name, 'white'))
            fg_color = gtk.gdk.color_parse("black")
            widget.modify_bg(gtk.STATE_ACTIVE, bg_color)
            widget.modify_base(gtk.STATE_NORMAL, bg_color)
            widget.modify_fg(gtk.STATE_NORMAL, fg_color)
            widget.modify_text(gtk.STATE_NORMAL, fg_color)
            widget.modify_text(gtk.STATE_INSENSITIVE, fg_color)
        elif name == 'readonly':
            widget.modify_bg(gtk.STATE_ACTIVE,
                    self.colors['bg_color_insensitive'])
            widget.modify_base(gtk.STATE_NORMAL,
                    self.colors['base_color_insensitive'])
            widget.modify_fg(gtk.STATE_NORMAL,
                    self.colors['fg_color_insensitive'])
            widget.modify_text(gtk.STATE_NORMAL,
                    self.colors['text_color_normal'])
            widget.modify_text(gtk.STATE_INSENSITIVE,
                    self.colors['text_color_normal'])
        else:
            widget.modify_bg(gtk.STATE_ACTIVE,
                    self.colors['bg_color_active'])
            widget.modify_base(gtk.STATE_NORMAL,
                    self.colors['base_color_normal'])
            widget.modify_fg(gtk.STATE_NORMAL,
                    self.colors['fg_color_normal'])
            widget.modify_text(gtk.STATE_NORMAL,
                    self.colors['text_color_normal'])
            widget.modify_text(gtk.STATE_INSENSITIVE,
                    self.colors['text_color_normal'])

    def invisible_set(self, value):
        widget = self._invisible_widget()
        if value and value != '0':
            self.visible = False
            widget.hide()
        else:
            self.visible = True
            widget.show()

    def _focus_out(self):
        if not self.field:
            return False
        if not self.visible:
            return False
        self.set_value(self.record, self.field)

    def _set_background(self, value):
        widget = self._color_widget()
        widget.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse(value))

    def _set_foreground(self, value):
        widget = self._color_widget()
        widget.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(value))

    def _set_font(self, value):
        widget = self._color_widget()
        widget.modify_font(pango.FontDescription(value))

    def _set_color(self, value):
        widget = self._color_widget()
        widget.modify_text(gtk.STATE_NORMAL,
            gtk.gdk.color_parse(value))
        widget.modify_text(gtk.STATE_INSENSITIVE,
            gtk.gdk.color_parse(value))

    def _format_set(self, record, field):
        functions = {
            'color': self._set_color,
            'fg': self._set_foreground,
            'bg': self._set_background,
            'font': self._set_font
            }
        attrs = record.expr_eval(field.get_state_attrs(record).
            get('states', {}))
        states = record.expr_eval(self.attrs.get('states', {})).copy()
        states.update(attrs)
        for attr in states.keys():
            if not states[attr]:
                continue
            key = attr.split('_')
            if key[0] == 'field':
                key = key[1:]
            if key[0] == 'label':
                continue
            if isinstance(states[attr], basestring):
                key.append(states[attr])
            if key[0] in functions:
                if len(key) != 2:
                    raise ValueError(FORMAT_ERROR + attr)
                functions[key[0]](key[1])

    def display(self, record, field):
        if not field:
            self._readonly_set(self.attrs.get('readonly', True))
            self.invisible_set(self.attrs.get('invisible', False))
            self._required_set(False)
            return
        states = field.get_state_attrs(record)
        readonly = self.attrs.get('readonly', states.get('readonly', False))
        if self.view.screen.readonly:
            readonly = True
        self._readonly_set(readonly)

        # ABD: Seems to be related to a color fix (c24c86dc)
        invalidity = field.get_state_attrs(record).get('invalid', False)
        if readonly:
            self.color_set('readonly')
        elif invalidity and invalidity != 'required':
            self.color_set('invalid')
        elif invalidity and invalidity == 'required':
            self.color_set('required')
        else:
            self.color_set('normal')

        # ABD: See #3428
        self._format_set(record, field)

        widget_class(self.widget, 'readonly', readonly)
        self._required_set(not readonly and states.get('required', False))
        widget_class(
            self.widget, 'required',
            not readonly and states.get('required', False))
        invalid = states.get('invalid', False)
        widget_class(self.widget, 'invalid', not readonly and invalid)
        self.invisible_set(self.attrs.get(
                'invisible', states.get('invisible', False)))

    def set_value(self, record, field):
        pass


class TranslateDialog(NoModal):

    def __init__(self, widget, languages, readonly):
        NoModal.__init__(self)
        self.widget = widget
        self.win = gtk.Dialog(_('Translation'), self.parent,
            gtk.DIALOG_DESTROY_WITH_PARENT)
        self.win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.win.set_icon(TRYTON_ICON)
        self.win.connect('response', self.response)

        self.accel_group = gtk.AccelGroup()
        self.win.add_accel_group(self.accel_group)

        self.win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.win.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK).add_accelerator(
            'clicked', self.accel_group, gtk.keysyms.Return,
            gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        tooltips = common.Tooltips()

        self.widgets = {}
        table = gtk.Table(len(languages), 4)
        table.set_homogeneous(False)
        table.set_col_spacings(3)
        table.set_row_spacings(2)
        table.set_border_width(1)
        for i, language in enumerate(languages):
            if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL:
                label = _(':') + language['name']
            else:
                label = language['name'] + _(':')
            label = gtk.Label(label)
            label.set_alignment(1.0, 0.0 if self.widget.expand else 0.5)
            table.attach(label, 0, 1, i, i + 1, xoptions=gtk.FILL)

            context = dict(
                language=language['code'],
                fuzzy_translation=False,
                )
            try:
                value = RPCExecute('model', self.widget.record.model_name,
                    'read', [self.widget.record.id], [self.widget.field_name],
                    context={'language': language['code']}
                    )[0][self.widget.field_name]
            except RPCException:
                return
            context['fuzzy_translation'] = True
            try:
                fuzzy_value = RPCExecute('model',
                    self.widget.record.model_name, 'read',
                    [self.widget.record.id], [self.widget.field_name],
                    context=context)[0][self.widget.field_name]
            except RPCException:
                return
            widget = self.widget.translate_widget()
            label.set_mnemonic_widget(widget)
            self.widget.translate_widget_set(widget, fuzzy_value)
            self.widget.translate_widget_set_readonly(widget, True)
            yopt = 0
            if self.widget.expand:
                yopt = gtk.EXPAND | gtk.FILL
            table.attach(widget, 1, 2, i, i + 1, yoptions=yopt)
            editing = gtk.CheckButton()
            editing.connect('toggled', self.editing_toggled, widget)
            editing.props.sensitive = not readonly
            tooltips.set_tip(editing, _('Edit'))
            table.attach(editing, 2, 3, i, i + 1, xoptions=gtk.FILL)
            fuzzy = gtk.CheckButton()
            fuzzy.set_active(value != fuzzy_value)
            fuzzy.props.sensitive = False
            tooltips.set_tip(fuzzy, _('Fuzzy'))
            table.attach(fuzzy, 4, 5, i, i + 1, xoptions=gtk.FILL)
            self.widgets[language['code']] = (widget, editing, fuzzy)

        tooltips.enable()
        vbox = gtk.VBox()
        vbox.pack_start(table, self.widget.expand, True)
        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        viewport.add(vbox)
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledwindow.set_shadow_type(gtk.SHADOW_NONE)
        scrolledwindow.add(viewport)
        self.win.vbox.pack_start(scrolledwindow, True, True)

        sensible_allocation = self.sensible_widget.get_allocation()
        self.win.set_default_size(int(sensible_allocation.width * 0.95),
            int(sensible_allocation.height * 0.95))

        self.register()
        self.win.show_all()
        common.center_window(self.win, self.parent, self.sensible_widget)

    def editing_toggled(self, editing, widget):
        self.widget.translate_widget_set_readonly(widget,
            not editing.get_active())

    def response(self, win, response):
        if response == gtk.RESPONSE_OK:
            for code, widget in self.widgets.iteritems():
                widget, editing, fuzzy = widget
                if not editing.get_active():
                    continue
                value = self.widget.translate_widget_get(widget)
                context = dict(
                    language=code,
                    fuzzy_translation=False,
                    )
                try:
                    RPCExecute('model', self.widget.record.model_name, 'write',
                        [self.widget.record.id], {
                            self.widget.field_name: value,
                            }, context=context)
                except RPCException:
                    pass
            self.widget.record.cancel()
            self.widget.view.display()
        self.destroy()

    def destroy(self):
        self.win.destroy()
        NoModal.destroy(self)


class TranslateMixin:

    def translate_button(self):
        button = gtk.Button()
        img = gtk.Image()
        img.set_from_stock('tryton-locale', gtk.ICON_SIZE_SMALL_TOOLBAR)
        button.set_image(img)
        button.set_relief(gtk.RELIEF_NONE)
        button.connect('clicked', self.translate)
        return button

    def translate(self, *args):
        self.view.set_value()
        if self.record.id < 0 or self.record.modified:
            common.message(
                _('You need to save the record before adding translations.'))
            return

        try:
            lang_ids = RPCExecute('model', 'ir.lang', 'search', [
                    ('translatable', '=', True),
                    ])
        except RPCException:
            return

        if not lang_ids:
            common.message(_('No other language available.'))
            return
        try:
            languages = RPCExecute('model', 'ir.lang', 'read', lang_ids,
                ['code', 'name'])
        except RPCException:
            return

        TranslateDialog(self, languages, self._readonly)

    def translate_widget(self):
        raise NotImplemented

    @staticmethod
    def translate_widget_set(widget, value):
        raise NotImplemented

    @staticmethod
    def translate_widget_get(widget):
        raise NotImplemented

    @staticmethod
    def translate_widget_set_readonly(widget, value):
        raise NotImplemented
