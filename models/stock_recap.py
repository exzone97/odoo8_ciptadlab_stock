from openerp import models, fields, api
from openerp.exceptions import ValidationError

class stock_picking_recap(models.Model):
    _name = 'stock.picking.recap'
    _description = ''

    recap_date  = fields.Datetime('Recap Date', required=True, default=lambda self: field.datetime.now())
    calculated_date = fields.Datetime('Calculated Date)
    # BELUM : calculate by diisi otomatis
    calculated_by = fields.Many2one('res.user', 'Calculated By')
    comfirm_date = fields.Datetime('Confirm Date')
    # BELUM : confirm by diisi otomatis
    confirm_by = fields.Many2one('res.user', 'Confirm By')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('calculated', 'Calculated'),
            ('confirmed','Confirmed')
        ],
        string='State',
        required=True,
        default='draft'
    )
    # BELUM : operation_count compute jumlah operation yang direkap dibawah rekapan ini
    operation_count = fields.Integer('Operation Count')
    # BELUM : recap_amount  nilai uang rekap ini, dihitung sebagai sum(subtotal) seluruh stock.picking.recap.line dibawahnya
    recap_amount = fields.Float('Recap Amount')
    stock_picking_type_id = fields.Many2one('stock.picking.type', required=True, ondeleted='restrict')
    stock_recap_line_ids = fields.One2many('stock.picking.recap.line', 'recap_id', 'Detail Recap')
    stock_move_ids = fields.One2many('stock.move','stock_recap_id', 'Stock Operation Detail')

class stock_picking_recap_line(models.Model):
    _name = 'stock.picking.recap.line'
    _description = ''

    recap_id = fields.Many2one('stock.picking.recap', 'Recap ID', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='restrict')
    qty = fields.Float('Quantity')
    unit_price = fields.Float('Unit Price')
    # subtotal computed qty*unit_price
    subtotal = fields.Float('Subtotal')

class stock_move(models.Model):

    _inherit = 'stock.move'

    stock_recap_id = fields.Many2one('stock.picking.recap', 'Stock ID')
