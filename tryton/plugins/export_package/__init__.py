import gettext

from tryton.action import Action
from tryton.common import RPCExecute, RPCException

_ = gettext.gettext


def add_to_exportpackage(data):
    model = data['model']
    record_ids = data['ids']

    if not model or not record_ids:
        return

    try:
        wiz_info, = RPCExecute('model', 'ir.model.data', 'search_read', [
                ('module', '=', 'cog_utils'),
                ('fs_id', '=', 'export_package_wizard'),
                ])
        Action.execute(wiz_info['db_id'], data, 'ir.action.wizard')
    except RPCException:
        return


def get_plugins(model):
    return [
        (_('Add to Export Package'), add_to_exportpackage),
        ]
