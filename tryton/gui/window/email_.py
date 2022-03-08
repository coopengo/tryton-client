# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gettext
import logging
import os

from gi.repository import GLib, GObject, Gtk

try:
    from gi.repository import GtkSpell
except ImportError:
    GtkSpell = None

from tryton.common import IconFactory, RPCException, RPCExecute, Tooltips
from tryton.common.richtext import (
    add_toolbar, get_content, register_format, set_content)
from tryton.common.underline import set_underline
from tryton.common.widget_style import widget_class
from tryton.config import CONFIG, TRYTON_ICON
from tryton.exceptions import TrytonError, TrytonServerError
from tryton.gui import Main
from tryton.gui.window.nomodal import NoModal

_ = gettext.gettext
logger = logging.getLogger(__name__)


class EmailEntry(Gtk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._completion = Gtk.EntryCompletion()
        self._completion.set_model(Gtk.ListStore(str, str))
        self._completion.set_text_column(0)
        self._completion.set_match_func(lambda *a: True)
        self._completion.connect('match-selected', self._match_selected)
        self.set_completion(self._completion)
        self.connect('changed', EmailEntry._changed)

    def _match_selected(self, completion, model, iter):
        self.set_text(model.get_value(iter, 1))
        self.set_position(-1)
        return True

    def _update_completion(self, text):
        if not self.props.window:
            return False
        if text != self.get_text():
            return False
        model = self._completion.get_model()
        if not text:
            model.clear()
            model.text = text
            return False
        if getattr(model, 'text', None) == text:
            return False

        def callback(results):
            try:
                results = results()
            except (TrytonError, TrytonServerError):
                logger.warning(
                    "Unable to complete email entry", exc_info=True)
                results = []
            if text != self.get_text():
                return False
            model.clear()
            for ratio, address, addresses in results:
                model.append([address, addresses])
            model.text = text
            # Force display of popup
            self.emit('changed')

        try:
            RPCExecute(
                'model', 'ir.email', 'complete', text, CONFIG['client.limit'],
                process_exception=False, callback=callback)
        except Exception:
            logger.warning(
                _("Unable to complete email entry"), exc_info=True)
        return False

    def _changed(self):
        def keypress():
            if not self.props.window:
                return
            self._update_completion()
        text = self.get_text()
        if self.get_position() >= len(text) - 1:
            GLib.timeout_add(300, self._update_completion, text)
        else:
            model = self._completion.get_model()
            model.clear()
            model.text = None


class Email(NoModal):

    def __init__(self, name, record, prints, template=None):
        super().__init__()
        self.record = record
        self.dialog = Gtk.Dialog(
            transient_for=self.parent, destroy_with_parent=True)
        Main().add_window(self.dialog)
        self.dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.dialog.set_icon(TRYTON_ICON)
        self.dialog.set_default_size(*self.default_size())
        self.dialog.connect('response', self.response)

        self.dialog.set_title(_('E-mail %s') % name)

        grid = Gtk.Grid(
            column_spacing=3, row_spacing=3,
            border_width=3)
        self.dialog.vbox.pack_start(grid, expand=True, fill=True, padding=0)

        label = Gtk.Label(
            set_underline(_("To:")), use_underline=True, halign=Gtk.Align.END)
        grid.attach(label, 0, 0, 1, 1)
        self.to = EmailEntry(hexpand=True, activates_default=True)
        widget_class(self.to, 'required', True)
        label.set_mnemonic_widget(self.to)
        grid.attach(self.to, 1, 0, 1, 1)

        label = Gtk.Label(
            set_underline(_("Cc:")), use_underline=True, halign=Gtk.Align.END)
        grid.attach(label, 0, 1, 1, 1)
        self.cc = EmailEntry(hexpand=True, activates_default=True)
        label.set_mnemonic_widget(self.cc)
        grid.attach(self.cc, 1, 1, 1, 1)

        label = Gtk.Label(
            set_underline(_("Bcc:")), use_underline=True, halign=Gtk.Align.END)
        grid.attach(label, 0, 2, 1, 1)
        self.bcc = EmailEntry(hexpand=True, activates_default=True)
        label.set_mnemonic_widget(self.bcc)
        grid.attach(self.bcc, 1, 2, 1, 1)

        label = Gtk.Label(
            set_underline(_("Subject:")),
            use_underline=True, halign=Gtk.Align.END)
        grid.attach(label, 0, 3, 1, 1)
        self.subject = Gtk.Entry(hexpand=True, activates_default=True)
        label.set_mnemonic_widget(self.subject)
        grid.attach(self.subject, 1, 3, 1, 1)

        self.body = Gtk.TextView()
        body_frame = Gtk.Frame()
        label = Gtk.Label(
            set_underline(_("Body")), use_underline=True, halign=Gtk.Align.END)
        label.set_mnemonic_widget(self.body)
        body_frame.set_label_widget(label)
        grid.attach(body_frame, 0, 4, 2, 1)
        body_box = Gtk.VBox(hexpand=True, vexpand=True)
        body_frame.add(body_box)
        register_format(self.body)
        body_toolbar = add_toolbar(self.body)
        body_box.pack_start(body_toolbar, expand=False, fill=True, padding=0)
        body_box.pack_start(self.body, expand=True, fill=True, padding=0)

        if GtkSpell and CONFIG['client.spellcheck']:
            checker = GtkSpell.Checker()
            checker.attach(self.body)
            language = os.environ.get('LANGUAGE', 'en')
            try:
                checker.set_language(language)
            except Exception:
                logger.error(
                    'Could not set spell checker for "%s"', language)
                checker.detach()

        attachments_box = Gtk.HBox()
        grid.attach(attachments_box, 0, 5, 2, 1)

        print_frame = Gtk.Frame(shadow_type=Gtk.ShadowType.NONE)
        print_frame.set_label(_("Reports"))
        attachments_box.pack_start(
            print_frame, expand=True, fill=True, padding=0)
        print_box = Gtk.VBox()
        print_frame.add(print_box)
        print_flowbox = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE)
        print_box.pack_start(
            print_flowbox, expand=False, fill=False, padding=0)
        self.print_actions = {}
        for print_ in prints:
            print_check = Gtk.CheckButton.new_with_mnemonic(
                set_underline(print_['name']))
            self.print_actions[print_['id']] = print_check
            print_flowbox.add(print_check)

        attachment_frame = Gtk.Frame(shadow_type=Gtk.ShadowType.NONE)
        attachment_frame.set_label(_("Attachments"))
        attachments_box.pack_start(
            attachment_frame, expand=True, fill=True, padding=0)
        try:
            attachments = RPCExecute('model', 'ir.attachment',
                'search_read', [
                    ('resource', '=', '%s,%s' % (
                            record.model_name, record.id)),
                    ['OR',
                        ('data', '!=', None),
                        ('file_id', '!=', None),
                        ],
                    ], 0, None, None, ['rec_name'],
                context=record.get_context())
        except RPCException:
            logger.error(
                'Could not fetch attachment for "%s"', record)
            attachments = []
        scrolledwindow = Gtk.ScrolledWindow()
        if len(attachments) > 2:
            scrolledwindow.set_size_request(-1, 100)
        attachment_frame.add(scrolledwindow)
        scrolledwindow.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.attachments = Gtk.TreeView()
        self.attachments.set_headers_visible(False)
        scrolledwindow.add(self.attachments)
        self.attachments.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.attachments.append_column(
            Gtk.TreeViewColumn(
                "Name", Gtk.CellRendererText(), text=0))
        model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_INT)
        for attachment in attachments:
            model.append((attachment['rec_name'], attachment['id']))
        self.attachments.set_model(model)
        self.attachments.set_search_column(0)

        file_frame = Gtk.Frame(shadow_type=Gtk.ShadowType.NONE)
        file_frame.set_label(_("Files"))
        attachments_box.pack_start(
            file_frame, expand=True, fill=True, padding=0)
        self.files = Gtk.VBox(spacing=6)
        file_frame.add(self.files)
        self._add_file_button()

        button_cancel = self.dialog.add_button(
            set_underline(_("Cancel")), Gtk.ResponseType.CANCEL)
        button_cancel.set_image(IconFactory.get_image(
                'tryton-cancel', Gtk.IconSize.BUTTON))

        button_send = self.dialog.add_button(
            set_underline(_("Send")), Gtk.ResponseType.OK)
        button_send.set_image(IconFactory.get_image(
                'tryton-send', Gtk.IconSize.BUTTON))
        self.dialog.set_default_response(Gtk.ResponseType.OK)

        self._fill_with(template)

        self.dialog.show_all()
        self.register()

    def _add_file_button(self):
        tooltips = Tooltips()
        box = Gtk.HBox(spacing=3)
        self.files.pack_start(box, expand=False, fill=True, padding=0)
        file_ = Gtk.FileChooserButton(title=_("Select File"))
        box.pack_start(file_, expand=True, fill=True, padding=0)
        button = Gtk.Button()
        button.set_image(IconFactory.get_image(
                'tryton-remove', Gtk.IconSize.BUTTON))
        tooltips.set_tip(button, _("Remove File"))
        button.set_sensitive(False)
        box.pack_start(button, expand=False, fill=True, padding=0)

        box.show_all()

        file_.connect('file-set', self._file_set, button)
        button.connect('clicked', self._file_remove)

    def _file_set(self, file_, button):
        button.set_sensitive(True)
        self._add_file_button()

    def _file_remove(self, button):
        self.files.remove(button.get_parent())

    def get_files(self):
        for box in self.files:
            file_ = list(box)[0]
            filename = file_.get_filename()
            if not filename:
                continue
            with open(filename, 'rb') as fp:
                data = fp.read()
            name = os.path.basename(filename)
            yield (name, data)

    def get_attachments(self):
        model, paths = self.attachments.get_selection().get_selected_rows()
        return [model[path][1] for path in paths]

    def _fill_with(self, template=None):
        try:
            if template:
                values = RPCExecute(
                    'model', 'ir.email.template', 'get',
                    template, self.record.id)
            else:
                values = RPCExecute(
                    'model', 'ir.email.template', 'get_default',
                    self.record.model_name, self.record.id)
        except RPCException:
            return
        self.to.set_text(', '.join(values.get('to', [])))
        self.cc.set_text(', '.join(values.get('cc', [])))
        self.bcc.set_text(', '.join(values.get('bcc', [])))
        self.subject.set_text(values.get('subject', ''))
        set_content(self.body, values.get('body', ''))
        print_ids = values.get('reports', [])
        for print_id, print_check in self.print_actions.items():
            print_check.set_active(print_id in print_ids)

    def validate(self):
        valid = True
        if not self.subject.get_text():
            valid = False
            widget_class(self.subject, 'invalid', True)
            self.subject.grab_focus()
        else:
            widget_class(self.subject, 'invalid', False)
        if not self.to.get_text():
            valid = False
            widget_class(self.to, 'invalid', True)
            self.to.grab_focus()
        else:
            widget_class(self.to, 'invalid', False)
        return valid

    def response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            if not self.validate():
                return
            to = self.to.get_text()
            cc = self.cc.get_text()
            bcc = self.bcc.get_text()
            subject = self.subject.get_text()
            body = get_content(self.body)
            files = list(self.get_files())
            reports = [
                id_ for id_, check in self.print_actions.items()
                if check.get_active()]
            attachments = self.get_attachments()
            try:
                RPCExecute(
                    'model', 'ir.email', 'send',
                    to, cc, bcc, subject, body,
                    files,
                    [self.record.model_name, self.record.id],
                    reports,
                    attachments)
            except RPCException:
                return
        self.destroy()

    def destroy(self):
        super().destroy()
        self.dialog.destroy()
