# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, today, nowdate, getdate, get_first_day, add_months
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
import math

class SalaryAdvance(Document):
	def validate(self):
		validate_workflow_states(self)
		self.update_defaults()
		self.get_basic_salary()
		self.validate_amounts()
		self.check_duplicates()
		notify_workflow_states(self)
		
	def on_submit(self):
		self.update_recovery_details()
		self.update_salary_structure()
		#self.update_salary_slip()
		self.post_journal_entry()
		notify_workflow_states(self)

	def on_cancel_after_draft(self):
		validate_workflow_states(self)
		notify_workflow_states(self)
		
	def on_cancel(self):
		# Deny cancelling if Journal Entry exists
		if self.reference and frappe.db.exists("Journal Entry", {"name":self.reference, "docstatus": ("<",2)}):
			frappe.throw(_('You need to cancel Journal Entry <a href="#Form/Journal Entry/{0}" target="_blank">{0}</a> first.').format(self.reference),title="Not Permitted")

		# Deny cancelling if Salary Slips already submitted
		for ssl in frappe.get_all("Salary Detail", fields=["parent"], filters={"reference_number": self.name, "salary_component": self.salary_component, "parenttype": "Salary Slip", "docstatus": 1}):
			frappe.throw(_('Unable to cancel as salary is already processed. Reference#<u><a href="#Form/Salary Slip/{0}" target="_blank">{0}</a></u>').format(ssl.parent), title="Invalid Operation")

		self.update_salary_structure(True)
		#self.update_salary_slip(True)
		notify_workflow_states(self)

	def update_defaults(self):
		self.posting_date     = nowdate()
		self.salary_component = "Salary Advance Deduction"
		
		if self.docstatus < 2:
			self.reference = None
		# Following code commented by SHIV on 2020/10/04
		#if self.docstatus == 0 and self.workflow_state == "Approved":
		#	self.workflow_state = "Waiting Approval"

	def validate_amounts(self):
		if flt(self.total_claim) > flt(self.max_advance_limit):
			frappe.throw(_("Advance requested cannot be more than maximum limit <b>Nu. {0}/-</b>").format("{:,.2f}".format(self.max_advance_limit)), title="Invalid Data")
		elif flt(self.total_claim) <= 0:
			frappe.throw(_("Advance Amount Requested should be greater than zero"), title="Invalid Data")

	def check_duplicates(self):
		##### Ver 3.0.190204 Beings, follow code commented by SHIV on 2019/02/04
		# as per NRDCL, employee can avail advance more than once as long as they do not have any due from earlier advance 
		'''
		# Checking for duplicate requests withing the fiscal_year
		for d in frappe.db.sql("select * from `tabSalary Advance` where employee = '{0}' and year(posting_date) = {1} and docstatus=1".format(self.employee, getdate(self.posting_date).year), as_dict=True):
			frappe.throw(_('You have already taken advance for the fiscal year {0} via <a href="#Form/Salary Advance/{1}" target="_blank">{1}</a> on {2}').format(getdate(self.posting_date).year, d.name, getdate(self.posting_date).strftime("%B %d, %Y")), title="Duplicate Entry")
		'''
		##### Ver 3.0.190204 Ends
		
		# Checking for unsettled advances
		sst_doc = frappe.get_doc("Salary Structure",frappe.db.get_value('Salary Structure', {'employee': self.employee, 'is_active' : 'Yes'}, "name"))
		for d in sst_doc.deductions:
			if d.salary_component == self.salary_component and flt(d.total_outstanding_amount) > 0:
				frappe.throw(_("Please settle your outstanding amount from previous advance of Nu.{0}/-").format("{:,.2f}".format(d.total_outstanding_amount)), title="Not Permitted")

	def update_recovery_details(self):
		flag     = 0
		self.recovery_start_date = get_first_day(self.posting_date)

		ssl = frappe.db.sql("""
					select
						name,
						docstatus,
						str_to_date(concat(yearmonth,"01"),"%Y%m%d") as salary_month
					from `tabSalary Slip`
					where employee = '{0}'
					and str_to_date(concat(yearmonth,"01"),"%Y%m%d") >= '{1}'
					and docstatus != 2
					order by yearmonth desc limit 1
		""".format(self.employee,str(self.recovery_start_date)),as_dict=True)
		for ss in ssl:
			if not flag:
				flat = 1
				self.recovery_start_date = add_months(str(ss.salary_month),1)
		self.db_set("recovery_start_date", self.recovery_start_date)

	# Commented because of permission issue to read salary structure of employees     
	'''
	def update_recovery_details(self):
		flag     = 0
		self.recovery_start_date = get_first_day(self.posting_date)

		ssl = frappe.db.sql("""
				select
					name,
					docstatus,
					str_to_date(concat(yearmonth,"01"),"%Y%m%d") as salary_month
				from `tabSalary Slip`
				where employee = '{0}'
				and str_to_date(concat(yearmonth,"01"),"%Y%m%d") >= '{1}'
				and docstatus = 0
				order by yearmonth limit 1
		""".format(self.employee,str(self.recovery_start_date)),as_dict=True)

		if len(ssl):
			for ss in ssl:
				if not flag:
					flag = 1
					self.recovery_start_date = str(ss.salary_month)
		else:
			ssl = frappe.db.sql("""
					select
						name,
						docstatus,
						str_to_date(concat(yearmonth,"01"),"%Y%m%d") as salary_month
					from `tabSalary Slip`
					where employee = '{0}'
					and str_to_date(concat(yearmonth,"01"),"%Y%m%d") >= '{1}'
					and docstatus = 1
					order by yearmonth desc limit 1
			""".format(self.employee,str(self.recovery_start_date)),as_dict=True)
			for ss in ssl:
				if not flag:
					flat = 1
					self.recovery_start_date = add_months(str(ss.salary_month),1)
		self.db_set("recovery_start_date", self.recovery_start_date)
	'''
		
	def update_salary_structure(self, cancel=False):
		if cancel:
			rem_list = []
			if self.salary_structure:
				doc = frappe.get_doc("Salary Structure", self.salary_structure)
				for d in doc.get("deductions"):
					if d.salary_component == self.salary_component and self.name in (d.reference_number, d.ref_docname):
						rem_list.append(d)

				[doc.remove(d) for d in rem_list]
				doc.save(ignore_permissions=True)
		else:
			if frappe.db.exists("Salary Structure", {"employee": self.employee, "is_active": "Yes"}):
				doc = frappe.get_doc("Salary Structure", {"employee": self.employee, "is_active": "Yes"})
				row = doc.append("deductions",{})
				row.salary_component        = self.salary_component
				row.from_date               = self.recovery_start_date
				row.to_date                 = self.recovery_end_date
				row.amount                  = flt(self.monthly_deduction)
				row.default_amount          = flt(self.monthly_deduction)
				row.reference_number        = self.name
				row.ref_docname             = self.name
				row.total_deductible_amount = flt(self.total_claim)
				row.total_deducted_amount   = 0
				row.total_outstanding_amount= flt(self.total_claim)
				row.total_days_in_month     = 0
				row.working_days            = 0
				row.leave_without_pay       = 0
				row.payment_days            = 0
				doc.save(ignore_permissions=True)
				self.db_set("salary_structure", doc.name)
			else:
				frappe.throw(_("No active salary structure found for employee {0} {1}").format(self.employee, self.employee_name), title="No Data Found")

	# Commented out because of permission issue to read salary structure
	'''
	def update_salary_slip(self, cancel=False):
		ssl = frappe.db.sql("""
				select
					name,
					docstatus,
					str_to_date(concat(yearmonth,"01"),"%Y%m%d") as salary_month
				from `tabSalary Slip`
				where employee = '{0}'
				and str_to_date(concat(yearmonth,"01"),"%Y%m%d") >= '{1}'
				and docstatus = 0
				order by yearmonth
		""".format(self.employee,str(self.recovery_start_date)),as_dict=True)
		for ss in ssl:
			doc = frappe.get_doc("Salary Slip", ss.name)
			doc.save(ignore_permissions=True)
	'''
	
	def get_basic_salary(self):
		if self.employee:
			# Get basic pay from the active salary structure
			sst_doc = frappe.get_doc("Salary Structure",frappe.db.get_value('Salary Structure', {'employee': self.employee, 'is_active' : 'Yes'}, "name"))
			for d in sst_doc.earnings:
				if d.salary_component == 'Basic Pay':
					self.basic_pay  = flt(d.amount)

			# Get advance settings from employee group master
			self.employee_group = frappe.db.get_value("Employee", self.employee, "employee_group")
			doc = frappe.get_doc("Employee Group", self.employee_group)
			self.salary_advance_type = doc.salary_advance_type

			if doc.salary_advance_type:
				if doc.salary_advance_type == "Flat Amount":
					self.max_months_limit	= 0
					self.max_advance_limit  = flt(doc.salary_advance_limit)
					#self.total_claim		= flt(doc.salary_advance_limit)
				else:
					self.max_months_limit	= doc.salary_advance_max_months 
					
					if (flt(self.basic_pay) * flt(self.max_months_limit)) > flt(doc.salary_advance_limit):
						self.max_advance_limit = flt(doc.salary_advance_limit)
					else:
						self.max_advance_limit 	= flt(self.basic_pay) * flt(self.max_months_limit)

					#self.total_claim       = flt(self.max_advance_limit)
			else:
				self.reset_amounts()
				frappe.throw(_("Salary Advance is not configured for {}").format(frappe.get_desk_link("Employee Group", self.employee_group)))
				
			if not self.deduction_month:
				self.deduction_month   = 12
			self.monthly_deduction = math.ceil(flt(self.total_claim) / cint(self.deduction_month))
		else:
			self.reset_amounts()
		
	def reset_amounts(self):
			self.basic_pay         = 0
			self.max_months_limit  = 0
			self.max_advance_limit = 0
			self.total_claim       = 0
			self.deduction_month   = 12
			self.monthly_deduction = 0

	def post_journal_entry(self):
		expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		ic_account = frappe.db.get_single_value("HR Accounts Settings", "employee_advance_salary")

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "Salary Advance (" + self.name + ")"
		je.voucher_type = 'Journal Entry'
		je.naming_series = 'Journal Entry'
		je.remark = 'Payment against : ' + self.name;
		je.posting_date = self.posting_date
		je.branch = self.branch

		je.append("accounts", {
				"account":ic_account,
				"business_activity": self.business_activity,
				"reference_name": self.name,
				"reference_type": "Salary Advance",
				"cost_center": self.cost_center,
				"debit_in_account_currency": flt(self.total_claim),
				"debit": flt(self.total_claim),
				"party_type": "Employee",
				"party": self.employee
		})
		
		je.append("accounts", {
				"account": expense_bank_account,
				"business_activity": self.business_activity,
				"reference_type": "Salary Advance",
				"reference_name": self.name,
				"cost_center": self.cost_center,
				"credit_in_account_currency": flt(self.total_claim),
				"credit": flt(self.total_claim),
		})
			
		je.insert()
		self.db_set("reference", je.name)

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabSalary Advance`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabSalary Advance`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabSalary Advance`.advance_approver = "{user}" and `tabSalary Advance`.workflow_state != "Draft")
	)""".format(user=user)

