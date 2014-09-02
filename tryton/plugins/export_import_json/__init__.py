import gtk
import re
import pango
import gettext

from tryton.common import TRYTON_ICON
from tryton.common import RPCExecute, RPCException, file_selection
from tryton.gui.window.nomodal import NoModal

_ = gettext.gettext


class LogDialog(NoModal):

    def __init__(self, name, result, message):
        super(LogDialog, self).__init__()
        self.name = name
        self.result = result


        self.win = gtk.Dialog(_('JSON Export'), self.parent,
            gtk.DIALOG_DESTROY_WITH_PARENT)
        self.win.set_icon(TRYTON_ICON)
        self.win.set_has_separator(False)
        self.textview = gtk.TextView()
        self.textview.set_wrap_mode(gtk.WRAP_WORD)
        self.table_tag = gtk.TextTagTable()
        self.text_buffer = gtk.TextBuffer(self.table_tag)
        self.textview.set_buffer(self.text_buffer)
        tag_values = (
            ('bold', 'weight', pango.WEIGHT_BOLD),
            ('italic', 'style', pango.STYLE_ITALIC),
            ('underline', 'underline', pango.UNDERLINE_SINGLE),
            ('left', 'justification', gtk.JUSTIFY_LEFT),
            ('center', 'justification', gtk.JUSTIFY_CENTER),
            ('right', 'justification', gtk.JUSTIFY_RIGHT),
            ('fill', 'justification', gtk.JUSTIFY_FILL),
            )
        self.text_tags = {}
        for tag, name, prop in tag_values:
            self.text_tags[tag] = gtk.TextTag(tag)
            self.text_tags[tag].set_property(name, prop)
            self.table_tag.add(self.text_tags[tag])
        self.set_buffer(message)
        self.textview.set_sensitive(False)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(self.textview)
        self.win.vbox.pack_start(scroll, expand=True, fill=True)

        but_ok = gtk.Button(_('_Save'))
        img_save = gtk.Image()
        img_save.set_from_stock('tryton-save', gtk.ICON_SIZE_BUTTON)
        but_ok.set_image(img_save)
        self.win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.win.add_action_widget(but_ok, gtk.RESPONSE_OK)
        self.win.connect('response', self.response)
        but_ok.grab_focus()

        sensible_allocation = self.sensible_widget.get_allocation()
        self.win.set_default_size(int(sensible_allocation.width * 0.95),
            int(sensible_allocation.height * 0.95))
        self.register()
        self.win.show_all()

    def destroy(self):
        self.win.destroy()
        super(LogDialog, self).destroy()

    def response(self, win, response_id):
        if response_id == gtk.RESPONSE_OK:
            filename = file_selection(_('Save As...'), self.name,
                action=gtk.FILE_CHOOSER_ACTION_SAVE)
            if filename:
                with open(filename, 'wb') as fp:
                    fp.write(self.result)
        self.destroy()

    def show(self):
        self.win.show()

    def hide(self):
        self.win.hide()

    def set_buffer(self, value):
        text_buffer, deserial = self.parser_from_text_markup(value)
        self.text_buffer.deserialize(self.text_buffer, deserial,
            self.text_buffer.get_start_iter(),
            text_buffer.serialize(text_buffer,
                "application/x-gtk-text-buffer-rich-text",
                text_buffer.get_start_iter(), text_buffer.get_end_iter()))

    def parser_from_text_markup(self, text):
        '''Parser from text markup to rich text view'''
        text_buffer = gtk.TextBuffer(self.table_tag)
        text_buffer.set_text(text)
        tags = []
        open_re = '<(?P<tag>\w{1,4})(?P<attrs> .+?)?>'
        create_mark = lambda pos: text_buffer.create_mark(None,
            text_buffer.get_iter_at_offset(pos), True)
        tag_names = {'b': 'bold', 'i': 'italic', 'u': 'underline',
            'p': 'justify', 'size': 'size', 'font_family': 'font_family',
            'foreground': 'foreground', 'background': 'background'}
        while re.search(open_re, text):
            data_open = re.search(open_re, text)
            tag = data_open.group('tag')
            attributes = data_open.group('attrs')
            text = re.sub(open_re, '', text, 1)
            text_buffer.delete(text_buffer.get_iter_at_offset(
                data_open.start()), text_buffer.get_iter_at_offset(
                    data_open.end()))
            close_re = '</%s>' % tag
            data_close = re.search(close_re, text)
            if data_close:
                text = re.sub(close_re, '', text, 1)
                text_buffer.delete(text_buffer.get_iter_at_offset(
                    data_close.start()), text_buffer.get_iter_at_offset(
                        data_close.end()))
                start = create_mark(data_open.start())
                end = create_mark(data_close.start())
                if tag in ('b', 'i', 'u'):
                    tags.append((start, end, tag_names[tag], None))
                elif tag == 'p':
                    val = re.search("align='(\w{,6})'", attributes)
                    if val:
                        tags.append((start, end, tag_names[tag], val.group(1)))
                elif tag == 'span':
                    attrs_re = " ([\w_]{4,11})='(.+?)'"
                    while re.search(attrs_re, attributes):
                        data = re.search(attrs_re, attributes)
                        att, val = data.group(1), data.group(2)
                        attributes = re.sub(attrs_re, '', attributes, 1)
                        tags.append((start, end, tag_names[att], val))
        for start, end, tag, value in tags:
            start = text_buffer.get_iter_at_mark(start)
            end = text_buffer.get_iter_at_mark(end)
            if tag in ('bold', 'italic', 'underline'):
                text_buffer.apply_tag(self.text_tags[tag], start, end)
            elif tag in ('font_family', 'size', 'foreground', 'background'):
                text_buffer.apply_tag(self.gen_tag(value, tag), start, end)
            else:  # tag <p>
                line = text_buffer.get_iter_at_line(start.get_line())
                text_buffer.apply_tag_by_name(value, line, end)
        self.text_buffer.set_text('')
        deserial = self.text_buffer.register_deserialize_tagset()
        return text_buffer, deserial


def export_json(data):
    model = data['model']
    record_id = data['id']
    try:
        name, result, export_log = RPCExecute('model', model, 'export_json',
            record_id)
    except RPCException:
        return
    LogDialog(name, result, export_log)


def import_json(data):
    model = data['model']
    filename = file_selection(_('Open...'))
    if filename:
        with open(filename, 'rb') as fp:
            values = fp.read()
        try:
            RPCExecute('model', model, 'import_json', values)
        except RPCException:
            return


def get_plugins(model):
    return [
        (_('Export JSON'), export_json),
        (_('Import JSON'), import_json),
        ]
