from odoo import api,models,Command

class AccountMove(models.Model):
    _inherit = 'estate.property'

    def do_sold(self):
        print('This is child class')

        vals = {
            'partner_id': self.buyer_id.id,
            'move_type':'out_invoice',

        }

        self.env['account.move'].create({
            'partner_id': self.buyer_id.id,
            'move_type':'out_invoice',
            'line_ids': [
                Command.create({
                    'name': '营业税',
                    'quantity': 1,
                    'price_unit': self.selling_price * 0.06,
                }),
                Command.create({
                    'name': '杂项',
                    'quantity': 1,
                    'price_unit': 100,
                }),
             ]
            })



        return super().do_sold()
