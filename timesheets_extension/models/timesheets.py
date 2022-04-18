from odoo import api, fields, models, _
from odoo.exceptions import UserError

# configurable variables

days_weekend = [5, 6]
"""list of weekend days"""

cst_leave = 1.5
"""multiplication of additional tasks hours not in weekend days by this constant"""

cst_leave_week_end = 2
"""multiplication of additional task hours in weekend days by this constant"""

class TimesheetExtension(models.Model):
    _inherit = "account.analytic.line"

    work_type = fields.Selection([
        ('working_hours', 'During working hours'),
        ('requested_project_manager', 'Overtime hours'),
        # ('personal_effort', 'Personal effort'),
    ], default='working_hours', string='DAMMAK')
    """field to present the Work Type of tasks"""
    state = fields.Selection([
        ('empty', ''),
        ('to_be_validated', 'To Be Validated'),
        ('refused', 'Refused'),
        ('validated', 'Validated')
    ], default='empty', string='State')
    """field to present the state of tasks"""

    validation=fields.Text(string="Validation", compute="validation_state_beta")

    leave_id = fields.Integer(String="Leave of Timesheet Validation")
    """field to save the id of the allocation request after validation"""
    def validation_state_beta(self):
        list=[]
        list_hours_day = []
        dict_final={}
        for rec in self:
            rec.validation=rec.date
            if rec.work_type=="working_hours":
                list_hours_day.append(rec.unit_amount)
                list.append(rec.date)

        for x,y in zip(list,list_hours_day):
            if x in dict_final:
                dict_final[x] = y+dict_final[x]
            else:
                dict_final[x]=y
    
        for rec in self:
            for key , value in dict_final.items():
                if rec.date == key :
                    if value == 8.0 :
                        rec.validation = "valide"
                    elif value > 8.0 :
                        rec.validation ="plus des heurs de travail"
                    elif value < 8.0 :
                        rec.validation ="manque des heurs de travail"
                    else:
                        rec.validation ="absent"
    def action_send_mail_validation(self):
        """
            Function to send an Email in the Validate action of Project Manager on Additional Tasks
        """
        template_id = self.env.ref('timesheets_extension.email_template_validation').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def action_send_mail_refuse(self):
        """
            Function to send an Email in the Refuse action of Project Manager on Additional Tasks
        """
        template_id = self.env.ref('timesheets_extension.email_template_refusing_validation').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def action_send_mail_cancel(self):
        """
            Function to send an Email in the Cancel action of Project Manager on Validated Additional Tasks
        """
        template_id = self.env.ref('timesheets_extension.email_template_cancel_validation').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def action_send_mail_reset(self):
        """
            Function to send an Email in the Reset action of Project Manager on Refused Additional Tasks
        """
        template_id = self.env.ref('timesheets_extension.email_template_reset_validation').id
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)

    def allocation_leaves(self):
        """
        function to make an allocation request in Time Off after validation of an additional task
        """
        try:
            context = self._context
            current_uid = context.get('uid')  # the id of the user
            # search in holiday's types to find the id of "Compensatory Days"
            leave_type = self.env['hr.leave.type'].search([])
            type_id = 0
            for leave in leave_type:
                if leave.display_name == "Compensatory Days" or leave.display_name == "Jours de compensation":
                    type_id = leave.id
                    break
            # if not, create a new type named "Compensatory Days"
            if type_id == 0:
                new_leave_type = self.env['hr.leave.type'].create({
                    'name': "Compensatory Days",
                    'request_unit': 'hour',
                    'allocation_type': 'fixed_allocation',
                    'validation_type': 'both',
                    'responsible_id': current_uid,
                })
                type_id = new_leave_type.id
            # create allocation request in Time Off
            day = self.date.weekday()
            if day in days_weekend:
                number_hours = self.unit_amount * cst_leave
            else:
                number_hours = self.unit_amount
            # a description for allocation requests to inform  about the validated task
            alloc_src = 'Extra Work for requested task: ' + str(self.task_id.name) + " (id=" + str(self.id) + ")"
            leave = self.env['hr.leave.allocation'].create({
                'name': alloc_src,
                'holiday_type': 'employee',
                'employee_id': self.employee_id.id,
                'holiday_status_id': type_id,
                'number_of_hours_display': number_hours,
            })
            leave.sudo().action_validate()
            self.leave_id = leave.id
        except Exception as e:
            raise e

    def cancel_allocation_leaves(self):
        """
        function to cancel the allocation request in Time Off if the project manager mistakenly validate a task
        """
        try:
            leave_cancel = self.env['hr.leave.allocation'].browse(self.leave_id)
            leave_cancel.sudo().action_refuse()
            leave_cancel.sudo().action_draft()
            leave_cancel.sudo().unlink()
        except Exception as e:
            raise e

    def action_validate_state(self):
        """
        function to validate the additional task status
        """
        for rec in self:
            if rec.state == 'to_be_validated':
                rec.state = 'validated'
                rec.allocation_leaves()
                rec.action_send_mail_validation()

    def action_cancel_validation_state(self):
        """
        function to cancel the validation of the additional task status
        """
        for rec in self:
            if rec.state == 'validated':
                rec.state = 'to_be_validated'
                rec.cancel_allocation_leaves()
                rec.action_send_mail_cancel()

    def action_refuse_validation_state(self):
        """
        function to refuse the validation of the additional task status
        """
        for rec in self:
            if rec.state == 'to_be_validated':
                rec.state = 'refused'
                rec.action_send_mail_refuse()

    def action_reset_validation_state(self):
        """
        function to reset the validation of the additional task status
        """
        for rec in self:
            if rec.state == 'refused':
                rec.state = 'to_be_validated'
                rec.action_send_mail_reset()

    @api.model
    def create(self, values):
        """\
        Override to the create function \n
        when the work type is an additional task, the status field will be To Be Validated by default
        """
        if values.get('work_type') == 'requested_project_manager':
            values['state'] = 'to_be_validated'
        # if values.get('work_type') == 'personal_effort':
        #     values['state'] = 'to_be_validated'
        res = super(TimesheetExtension, self).create(values)
        return res

    def write(self, values):
        """
        Override to the write function
        """
        res = super(TimesheetExtension, self).write(values)
        if values.get('work_type') == 'working_hours':
            self.write({'state': 'empty'})
        if values.get('work_type') == 'requested_project_manager':
            self.write({'state': 'to_be_validated'})
        # if values.get('work_type') == 'personal_effort':
        #     self.write({'state': 'to_be_validated'})
        return res

    def unlink(self):
        """
        Override to the unlink function \n
        a validated or refused task cannot be deleted
        """
        state_description = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        for task in self.filtered(lambda timesheet: timesheet.state not in ['empty', 'to_be_validated']):
            raise UserError(_('You cannot delete a task which is in %s state.') % (state_description.get(task.state),))
        return super(TimesheetExtension, self).unlink()
