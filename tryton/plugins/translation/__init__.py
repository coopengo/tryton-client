# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gettext

from tryton.common import MODELACCESS
from tryton.gui.window import Window

_ = gettext.gettext


def translate_view(datas):
    model = datas['model']
    Window.create('ir.translation',
        res_id=False,
        domain=[('model', '=', model)],
        mode=['tree', 'form'],
        name=_('Translate view'))


def get_plugins(model):
    access = MODELACCESS['ir.translation']
    if access['read'] and access['write']:
        return [
            (_('Translate view'), translate_view),
            ]
    else:
        return []
