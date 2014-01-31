import gtk
import gettext

from tryton.common import RPCExecute, RPCException, file_selection

_ = gettext.gettext


def export_json(data):
    model = data['model']
    record_id = data['id']
    try:
        name, result = RPCExecute('model', model, 'export_json', record_id)
    except RPCException:
        return
    filename = file_selection(_('Save As...'), name,
        action=gtk.FILE_CHOOSER_ACTION_SAVE)
    if filename:
        with open(filename, 'wb') as fp:
            fp.write(result)


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
