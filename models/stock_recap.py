from openerp import models, fields, api
from openerp.exceptions import ValidationError
from datetime import datetime

class stock_picking_recap(models.Model):
	_name = 'stock.picking.recap'
	_description = ''

	recap_date  = fields.Datetime('Recap Date', required=True, default=lambda self: datetime.now())
	calculated_date = fields.Datetime('Calculated Date')
	calculated_by = fields.Many2one('res.users', 'Calculated By')
	comfirm_date = fields.Datetime('Confirm Date')
	confirm_by = fields.Many2one('res.users', 'Confirm By', readonly=True)
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
	stock_move_ids = fields.One2many('stock.move','stock_recap_id', 'Stock Operation Detail', readonly=True)
	stock_move_list = fields.Char('List stock move', invisible=True)
# OVERRIDE ------------------------------------------------------------------------------------------------------------------

	@api.model
	def create(self,vals):
		rec = super(stock_picking_recap, self).create(vals)
		for record in self.stock_recap_line_ids:
			record.write({
					'recap_id': self.id,
				})

		return rec
# ACTIONS ------------------------------------------------------------------------------------------------------------------

	@api.multi
	def action_calculated(self):
		context = self._context
		current_uid = context.get('uid')
		user = self.env['res.users'].browse(current_uid)
		return self.write({
			'state': 'calculated',
			'calculated_by': user.id,
			'calculated_date': datetime.now(),
		})

	@api.multi
	def action_confirm(self):
		context = self._context
		current_uid = context.get('uid')
		user = self.env['res.users'].browse(current_uid)

		return self.write({
			'state': 'confirmed',
			'confirm_by':user.id
		})

	@api.onchange('stock_picking_type_id')
	def onchange_type_id(self):
		if(self.stock_recap_line_ids != None) :
			stock_move = self.env['stock.move'].search([('stock_recap_id','=',self.stock_picking_type_id.id)])
			recap_line_obj = self.env['stock.picking.recap.line']
			for stock in stock_move:
				recap_line = recap_line_obj.create({
						'product_id': stock.product_id.id,
						# 'qty': stock.product_uom_qty,
					})
				print stock
				self.write({
						'stock_recap_line_ids': [(0,0,recap_line)],
					})



class stock_picking_recap_line(models.Model):
	_name = 'stock.picking.recap.line'
	_description = ''

	recap_id = fields.Many2one('stock.picking.recap', 'Recap ID', ondelete='cascade')
	product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='restrict')
	qty = fields.Float('Quantity')
	unit_price = fields.Float('Unit Price')
	subtotal = fields.Float('Subtotal',compute="_compute_subtotal")

	@api.multi
	@api.depends('qty','unit_price')
	def _compute_subtotal(self):
		for record in self:
			record.subtotal = record.qty * record.unit_price


class stock_move(models.Model):
	_inherit = 'stock.move'

	stock_recap_id = fields.Many2one('stock.picking.recap', 'Stock ID')
