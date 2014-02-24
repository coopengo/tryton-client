import gtk
import gettext

from tryton.common import TRYTON_ICON
from tryton.common import RPCExecute, RPCException
from tryton.gui.window.nomodal import NoModal

_ = gettext.gettext


class ExportPackageDialog(NoModal):

    def __init__(self, model, record_id, packages):
        super(ExportPackageDialog, self).__init__()
        self.model = model
        self.record_id = record_id

        self.win = gtk.Dialog(_('Choose Package'), self.parent,
            gtk.DIALOG_DESTROY_WITH_PARENT)
        self.win.set_icon(TRYTON_ICON)
        self.win.set_has_separator(False)

        table = gtk.Table(1, 2)
        self.win.vbox.pack_start(table, expand=True, fill=False, padding=0)
        label = gtk.Label(_('Select Package'))
        table.attach(label, 0, 1, 0, 1)
        store = gtk.ListStore(int, str)
        self.combo = gtk.ComboBox(store)
        cell = gtk.CellRendererText()
        self.combo.pack_start(cell, True)
        self.combo.add_attribute(cell, 'text', 1)
        table.attach(self.combo, 1, 2, 0, 1)

        for package in packages:
            store.append((package['id'], package['package_name']))

        self.win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        but_ok = gtk.Button(_('_OK'))
        img_save = gtk.Image()
        img_save.set_from_stock('tryton-save', gtk.ICON_SIZE_BUTTON)
        but_ok.set_image(img_save)
        self.win.add_action_widget(but_ok, gtk.RESPONSE_OK)
        self.win.connect('response', self.response)

        sensible_allocation = self.sensible_widget.get_allocation()
        self.win.set_default_size(int(sensible_allocation.width * 0.95),
            int(sensible_allocation.height * 0.95))
        self.register()
        self.win.show_all()

    def destroy(self):
        self.win.destroy()
        super(ExportPackageDialog, self).destroy()

    def response(self, win, response):
        if response == gtk.RESPONSE_OK:
            model = self.combo.get_model()
            active = self.combo.get_active()
            if active != -1:
                package_id = model[active][0]
                try:
                    RPCExecute('model', 'ir.export_package.item', 'create', [{
                                'to_export': '%s,%s' % (self.model,
                                    self.record_id),
                                'package': package_id,
                                },
                            ])
                except RPCException:
                    pass
        self.destroy()

    def show(self):
        self.win.show()

    def hide(self):
        self.win.hide()


def add_to_exportpackage(data):
    model = data['model']
    record_id = data['id']

    if not model or not record_id:
        return

    try:
        ids = RPCExecute('model', 'ir.export_package', 'search', [])
        packages = RPCExecute('model', 'ir.export_package', 'read', ids,
            ['id', 'package_name'])
        ExportPackageDialog(model, record_id, packages)
    except RPCException:
        return


def get_plugins(model):
    return [
        (_('Add to Export Package'), add_to_exportpackage),
        ]
