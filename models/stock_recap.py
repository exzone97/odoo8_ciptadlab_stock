from openerp import models, fields, api
from openerp.exceptions import ValidationError
import datetime
from dateutil.relativedelta import relativedelta

number_of_month = 3

class stock_picking_recap(models.Model):
	_name = 'stock.picking.recap'
	_description = ''

	recap_date  = fields.Datetime('Recap Date', required=True, default=lambda self: datetime.datetime.now())
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
	operation_count = fields.Integer('Operation Count', readonly=True)
	# BELUM : recap_amount  nilai uang rekap ini, dihitung sebagai sum(subtotal) seluruh stock.picking.recap.line dibawahnya
	recap_amount = fields.Float('Recap Amount', readonly=True)
	stock_picking_type_id = fields.Many2one('stock.picking.type', required=True, ondeleted='restrict', default=None)
	stock_recap_line_ids = fields.One2many('stock.picking.recap.line', 'recap_id', 'Detail Recap')
	stock_move_ids = fields.One2many('stock.move','stock_recap_id', 'Stock Operation Detail', readonly=True)
	stock_move_list = fields.Char('List stock move', invisible=True)
# OVERRIDE ------------------------------------------------------------------------------------------------------------------

	@api.model
	def create(self,vals):
		rec = super(stock_picking_recap, self).create(vals)
		count = 0
		for record in rec.stock_recap_line_ids:
			record.recap_id = rec.id
		picking_id = rec.stock_picking_type_id.id
		stock_move = self.env['stock.move'].search([('picking_type_id.id','=',picking_id)])
		for record in stock_move:
			count += 1
			record.stock_recap_id = rec.id
			print record.id
		rec.operation_count = count

		return rec
# ACTIONS ------------------------------------------------------------------------------------------------------------------

	@api.multi
	def action_calculated(self):
		context = self._context
		current_uid = context.get('uid')
		user = self.env['res.users'].browse(current_uid)
		total = 0
		for record in self.stock_recap_line_ids:
			total += record.subtotal
		return self.write({
			'state': 'calculated',
			'calculated_by': user.id,
			'calculated_date': datetime.datetime.now(),
			'recap_amount': total
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

	@api.one
	def action_get_avg(self):
		lines = self.stock_recap_line_ids
		for record in lines:
			count = 0
			unit_price = 0
			tanggal = datetime.datetime.now() - relativedelta(months = number_of_month)
			recap_lines_obj = self.env['stock.picking.recap.line'].search([('product_id','=',record.product_id.id),('create_date' ,'>',tanggal.strftime("%Y-%m-%d")),('unit_price','>',0)])
			for record2 in recap_lines_obj:
				unit_price += record2.unit_price
				count += 1
			if count == 0:
				unit_price = 0
			else:
				unit_price = unit_price / count	
			record.unit_price = unit_price

	@api.onchange('stock_picking_type_id')
	def onchange_type_id(self):
		if self.stock_recap_line_ids != None :	
			count = 0
			picking_id = self.stock_picking_type_id.id
			stock_move = self.env['stock.move'].search([('picking_type_id.id','=',picking_id),('stock_recap_id','=',False)])
			recap_line_obj = self.env['stock.picking.recap.line']
			lines = {}
			for stock in stock_move:
				count +=1
				if stock.product_id.id in lines:
					lines[stock.product_id.id]['qty'] += stock.product_uom_qty
					continue

				lines[stock.product_id.id] = {
					'product_id': stock.product_id.id,
					'qty': stock.product_uom_qty,
					'product_uom': stock.product_uom
				}
			for id, line in lines.items():
				recap_line_obj += recap_line_obj.new({
					'product_id': line['product_id'],
					'qty': line['qty'],
					'product_uom': line['product_uom']
				})
			self.stock_recap_line_ids = recap_line_obj
			self.operation_count = count

	"""
	def find_uom_by_product_id(self, product_id=False):

		if not product_id:
			return {}

		product = self.env['product.product'].browse(product_id)
		result = {
			'product_uom': product.uom_id.id
		}
		return {'value': result}
	"""

class stock_picking_recap_line(models.Model):
	_name = 'stock.picking.recap.line'
	_description = ''

	recap_id = fields.Many2one('stock.picking.recap', 'Recap ID', ondelete='cascade')
	product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='restrict')
	qty = fields.Float('Quantity')
	unit_price = fields.Float('Unit Price')
	subtotal = fields.Float('Subtotal',compute="_compute_subtotal")
	product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True, help="Default Unit of Measure used for all stock operation.")


	@api.multi
	@api.depends('qty','unit_price')
	def _compute_subtotal(self):
		for record in self:
			record.subtotal = record.qty * record.unit_price

	@api.onchange('unit_price')
	def _compute_recap_amount(self):
		self.subtotal = self.qty * self.unit_price 


class stock_move(models.Model):
	_inherit = 'stock.move'

	stock_recap_id = fields.Many2one('stock.picking.recap', 'Stock ID')
