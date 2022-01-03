# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gettext
import webbrowser

import tryton.rpc as rpc
from tryton.common import RPCExecute, RPCException
from tryton.common import message, selection, file_write, file_open
from tryton.config import CONFIG
from tryton.pyson import PYSONDecoder

_ = gettext.gettext


class Action(object):

    @staticmethod
    def exec_report(name, data, direct_print=False, context=None):
        if context is None:
            context = {}
        else:
            context = context.copy()
        context['direct_print'] = direct_print
        ids = data.get('ids', [])

        def callback(result):
            try:
                result = result()
            except RPCException:
                return
            type, data, print_p, name = result
            if not print_p and direct_print:
                print_p = True
            fp_name = file_write((name, type), data)
            file_open(fp_name, type, print_p=print_p)
        RPCExecute(
            'report', name, 'execute', ids, data, context=context,
            callback=callback)

    @staticmethod
    def execute(action, data, context=None, keyword=False):
        if isinstance(action, int):
            # Must be executed synchronously to avoid double execution
            # on double click.
            action = RPCExecute(
                'model', 'ir.action', 'get_action_value', action,
                context=context)
        if keyword:
            keywords = {
                'ir.action.report': 'form_report',
                'ir.action.wizard': 'form_action',
                'ir.action.act_window': 'form_relate',
                }
            action.setdefault('keyword', keywords.get(action['type'], ''))
        Action._exec_action(action, data, context=context)

    @staticmethod
    def _exec_action(action, data=None, context=None):
        from tryton.gui.window import Window
        if context is None:
            context = {}
        else:
            context = context.copy()
        if data is None:
            data = {}
        else:
            data = data.copy()
        if 'type' not in (action or {}):
            return

        context.pop('active_id', None)
        context.pop('active_ids', None)
        context.pop('active_model', None)

        def add_name_suffix(name, context=None):
            if not data.get('ids') or not data.get('model'):
                return name
            max_records = 5
            ids = list(filter(lambda id: id >= 0, data['ids']))[:max_records]
            if not ids:
                return name
            rec_names = RPCExecute('model', data['model'],
                'read', ids, ['rec_name'],
                context=context)
            name_suffix = _(', ').join([x['rec_name'] for x in rec_names])
            if len(data['ids']) > len(ids):
                name_suffix += _(',...')
            return _('%s (%s)') % (name, name_suffix)

        data['action_id'] = action['id']
        if action['type'] == 'ir.action.act_window':
            view_ids = []
            view_mode = None
            if action.get('views', []):
                view_ids = [x[0] for x in action['views']]
                view_mode = [x[1] for x in action['views']]
            elif action.get('view_id', False):
                view_ids = [action['view_id'][0]]

            action.setdefault('pyson_domain', '[]')
            ctx = {
                'active_model': data.get('model'),
                'active_id': data.get('id'),
                'active_ids': data.get('ids') or [],
            }
            ctx.update(rpc.CONTEXT)
            ctx['_user'] = rpc._USER
            decoder = PYSONDecoder(ctx)
            action_ctx = context.copy()
            action_ctx.update(
                decoder.decode(action.get('pyson_context') or '{}'))
            ctx.update(action_ctx)

            ctx['context'] = ctx
            decoder = PYSONDecoder(ctx)
            domain = decoder.decode(action['pyson_domain'])
            order = decoder.decode(action['pyson_order'])
            search_value = decoder.decode(action['pyson_search_value'] or '[]')
            tab_domain = [(n, decoder.decode(d), c)
                for n, d, c in action['domains']]

            name = action.get('name', '')
            if action.get('keyword', ''):
                name = add_name_suffix(name, action_ctx)

            res_model = action.get('res_model', data.get('res_model'))
            res_id = action.get('res_id', data.get('res_id'))
            limit = action.get('limit')
            if limit is None:
                limit = CONFIG['client.limit']

            Window.create(res_model,
                view_ids=view_ids,
                res_id=res_id,
                domain=domain,
                context=action_ctx,
                order=order,
                mode=view_mode,
                name=name,
                limit=limit,
                search_value=search_value,
                icon=(action.get('icon.rec_name') or ''),
                tab_domain=tab_domain,
                context_model=action['context_model'],
                context_domain=action['context_domain'])
        elif action['type'] == 'ir.action.wizard':
            name = action.get('name', '')
            if action.get('keyword', 'form_action') == 'form_action':
                name = add_name_suffix(name, context)
            Window.create_wizard(action['wiz_name'], data,
                direct_print=action.get('direct_print', False),
                name=name,
                context=context, icon=(action.get('icon.rec_name') or ''),
                window=action.get('window', False))

        elif action['type'] == 'ir.action.report':
            Action.exec_report(
                action['report_name'], data,
                direct_print=action.get('direct_print', False),
                context=context)

        elif action['type'] == 'ir.action.url':
            if action['url']:
                webbrowser.open(action['url'], new=2)

    @staticmethod
    def exec_keyword(keyword, data=None, context=None, warning=True,
            alwaysask=False):
        actions = []
        model_id = data.get('id', False)
        try:
            actions = RPCExecute('model', 'ir.action.keyword',
                'get_keyword', keyword, (data['model'], model_id))
        except RPCException:
            return False

        keyact = {}
        for action in actions:
            keyact[action['name'].split(' / ')[-1]] = action

        res = selection(_('Select your action'), keyact, alwaysask=alwaysask)
        if res:
            (name, action) = res
            Action.execute(action, data, context=context)
            return (name, action)
        elif not len(keyact) and warning:
            message(_('No action defined.'))
        return False
