# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from sql import Null
from sql.conditionals import Case

from trytond.model import ModelView, ModelSQL, MatchMixin, fields
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.cache import Cache

__all__ = ['Carrier', 'CarrierSelection']


class Carrier(ModelSQL, ModelView):
    'Carrier'
    __name__ = 'carrier'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    carrier_product = fields.Many2One('product.product', 'Carrier Product',
            required=True, domain=[
                ('type', '=', 'service'),
                ('template.type', '=', 'service'),
            ])
    carrier_cost_method = fields.Selection([
        ('product', 'Product Price'),
        ], 'Carrier Cost Method', required=True,
        help='Method to compute carrier cost')

    @staticmethod
    def default_carrier_cost_method():
        return 'product'

    def get_rec_name(self, name):
        return '%s - %s' % (self.party.rec_name, self.carrier_product.rec_name)

    def get_sale_price(self):
        'Compute carrier sale price with currency'
        User = Pool().get('res.user')
        if self.carrier_cost_method == 'product':
            user = User(Transaction().user
                or Transaction().context.get('user'))
            return self.carrier_product.list_price, user.company.currency.id
        return 0, None

    def get_purchase_price(self):
        'Compute carrier purchase price with currency'
        User = Pool().get('res.user')
        if self.carrier_cost_method == 'product':
            user = User(Transaction().user)
            return self.carrier_product.cost_price, user.company.currency.id
        return 0, None


class CarrierSelection(MatchMixin, ModelSQL, ModelView):
    'Carrier Selection'
    __name__ = 'carrier.selection'
    _get_carriers_cache = Cache('carrier.selection.get_carriers')

    sequence = fields.Integer('Sequence')
    active = fields.Boolean('Active')
    from_country = fields.Many2One('country.country', 'From Country',
        ondelete='RESTRICT')
    to_country = fields.Many2One('country.country', 'To Country',
        ondelete='RESTRICT')
    carrier = fields.Many2One('carrier', 'Carrier', required=True,
        ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super(CarrierSelection, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [Case((table.sequence == Null, 0), else_=1), table.sequence]

    @staticmethod
    def default_active():
        return True

    @classmethod
    def create(cls, *args, **kwargs):
        selections = super(CarrierSelection, cls).create(*args, **kwargs)
        cls._get_carriers_cache.clear()
        return selections

    @classmethod
    def write(cls, *args, **kwargs):
        super(CarrierSelection, cls).write(*args, **kwargs)
        cls._get_carriers_cache.clear()

    @classmethod
    def delete(cls, *args, **kwargs):
        super(CarrierSelection, cls).delete(*args, **kwargs)
        cls._get_carriers_cache.clear()

    @classmethod
    def get_carriers(cls, pattern):
        pool = Pool()
        Carrier = pool.get('carrier')

        key = tuple(sorted(pattern.iteritems()))
        carriers = cls._get_carriers_cache.get(key)
        if carriers is not None:
            return Carrier.browse(carriers)

        carriers = []
        for selection in cls.search([]):
            if selection.match(pattern):
                carriers.append(selection.carrier)

        cls._get_carriers_cache.set(key, map(int, carriers))
        return carriers
