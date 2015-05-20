import gettext

from tryton.common import RPCExecute, RPCException, file_selection
from tryton.action import Action

_ = gettext.gettext


def export_json(data):
    model = data['model']
    record_ids = data['ids']
    data['export_result'] = None
    if not model or not record_ids:
        return

    try:
        wiz_info, = RPCExecute('model', 'ir.model.data', 'search_read', [
                ('module', '=', 'cog_utils'),
                ('fs_id', '=', 'export_to_file'),
                ])
        Action.execute(wiz_info['db_id'], data, 'ir.action.wizard')
    except RPCException:
        return


def import_json(data):
    model = data['model']
    filename = file_selection(_('Open...'))
    if filename:
        with open(filename, 'rb') as fp:
            values = fp.read()
        try:
            RPCExecute('model', model, 'multiple_import_json', values)
        except RPCException:
            return


def get_plugins(model):
    return [
        (_('Export JSON'), export_json),
        (_('Import JSON'), import_json),
        ]
