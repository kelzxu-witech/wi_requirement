from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    user = fields.Many2one(
        'res.partner', string='User', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_type = fields.Selection([('requirements', 'Requirements'),
                                  ('order', 'Orders')],string='Type',default='order')
    Assignees_user = fields.Many2one(
        'res.users', string='Assignees', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    Assignees_signature = fields.Image('Assignees Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
    pic_signature = fields.Image('PIC Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
    attachment = fields.Char('attachment', default='-')

    @api.onchange('Assignees_user')
    def Assignees_user_change(self):
        self.sale_type = 'requirements'

    def has_to_be_signed(self, include_draft=False):
        return (self.state == 'sent' or self.state == 'draft') and not self.is_expired and self.require_signature and not self.signature

    @api.model
    def create(self, vals):
        if vals['sale_type'] == 'order':
            if vals.get('name', _('New')) == _('New'):
                seq_date = None
                if 'date_order' in vals:
                    seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                if 'company_id' in vals:
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                        'sale.order', sequence_date=seq_date) or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('sale.order', sequence_date=seq_date) or _('New')
        else:
            if vals.get('name', _('New')) == _('New'):
                seq_date = None
                if 'date_order' in vals:
                    seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                if 'company_id' in vals:
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                        'user.requirement', sequence_date=seq_date) or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('user.requirement', sequence_date=seq_date) or _('New')
        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        return result

    def _find_sales_mail_template(self,template_id,force_confirmation_template=False):
        if force_confirmation_template or (self.state == 'sale' and not self.env.context.get('proforma', False)):
            template_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
            template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
            if not template_id:
                template_id = self.env['ir.model.data'].xmlid_to_res_id('sale.mail_template_sale_confirmation', raise_if_not_found=False)
        if not template_id:
            template_id = self.env['ir.model.data'].xmlid_to_res_id('sale.email_template_edi_sale', raise_if_not_found=False)

        return template_id

    def _find_requirement_mail_template(self,template_id, force_confirmation_template=False):
        if force_confirmation_template or (self.state == 'sale' and not self.env.context.get('proforma', False)):
            template_id = int(self.env['ir.config_parameter'].sudo().get_param('wi_requirement.default_req_confirmation_template'))
            template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
            if not template_id:
                template_id = self.env['ir.model.data'].xmlid_to_res_id('wi_requirement.mail_template_requirement_confirmation', raise_if_not_found=False)
        if not template_id:
            template_id = self.env['ir.model.data'].xmlid_to_res_id('wi_requirement.email_template_edi_requirement', raise_if_not_found=False)

        return template_id
        

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False
        if self.sale_type == 'requirements':
            template_id = self._find_requirement_mail_template(template_id)
        else:
            template_id = self._find_sales_mail_template(template_id)

        return template_id

    @api.depends('state')
    def _compute_type_name(self):
        for record in self:
            if record.sale_type != 'requirements':
                record.type_name = _('Quotation') if record.state in ('draft', 'sent', 'cancel') else _('Sales Order')
            else:
                record.type_name = _('User Requirement')






