# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, money_in_words, getdate
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
from frappe.utils.data import add_days, date_diff
from frappe.model.mapper import get_mapped_doc
from datetime import timedelta
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class TravelAuthorization(Document):
	def validate(self):
		self.branch = frappe.db.get_value("Employee", self.employee, "branch")
		self.cost_center = frappe.db.get_value("Employee", self.employee, "cost_center")
		
		#if frappe.db.get_value("Employee", self.employee, "user_id") == self.supervisor:
		#        frappe.throw(_("Invalid supervisor"), title="Invalid Data")
		validate_workflow_states(self)
		self.validate_travel_dates()
		self.check_double_dates()
		self.assign_end_date()
		self.validate_advance()
		self.set_travel_period()
		notify_workflow_states(self)

	def validate_advance(self):
		self.advance_amount     = 0 if not self.need_advance else self.advance_amount
		self.advance_amount_nu  = 0 if not self.need_advance else self.advance_amount_nu
		self.advance_journal    = None if self.docstatus == 0 else self.advance_journal
	
	def create_copy(self):
		self.details = []
		for a in self.items:
			self.append("details", {"date": a.date, "halt": a.halt, "till_date": a.till_date, "no_days": a.no_days, "from_place": a.from_place, "halt_at": a.halt_at})

	def on_update(self):
		self.set_dsa_rate()
		self.check_double_dates()
		# Following code commented by SHIV on 2020/10/04
		'''
		if frappe.session.user != self.supervisor:
			if self.document_status == "Rejected":
				self.db_set("document_status", "")
			self.sendmail(frappe.db.get_value("Employee", {"user_id": self.supervisor}, "name"), "Travel Authorization Requested", str(self.employee_name) + " has requested you to verify and sign a " + str(frappe.get_desk_link("Travel Authorization", self.name)))
		elif self.document_status == "Rejected":
			self.sendmail(self.employee, "Travel Authorization Rejected" + str(self.name), "Following remarks has been added by the supervisor: \n" + str(self.reason))
		'''

	def before_submit(self):
		self.create_copy()

	def create_copy(self):
		self.details = []
		for a in self.items:
			self.append("details", {"date": a.date, "halt": a.halt, "till_date": a.till_date, "no_days": a.no_days, "from_place": a.from_place, "halt_at": a.halt_at})

	def on_submit(self):
		#self.get_status()
		#self.check_double_dates()
		#self.validate_submitter()
		self.validate_travel_dates()
		self.check_status()
		self.check_advance()
		self.create_attendance()
		# Following line commented by SHIV on 2020/10/04
		#self.sendmail(self.employee, "Travel Authorization Approved" + str(self.name), "Your " + str(frappe.get_desk_link("Travel Authorization", self.name)) + " has been approved by the supervisor")
		notify_workflow_states(self)

	def before_cancel(self):
		if self.advance_journal:
			for t in frappe.get_all("Journal Entry", ["name"], {"name": self.advance_journal, "docstatus": ("<",2)}):
				msg = '<b>Reference# : <a href="#Form/Journal Entry/{0}">{0}</a></b>'.format(t.name)
				frappe.throw(_("Advance payment for this transaction needs to be cancelled first.<br>{0}").format(msg),title='<div style="color: red;">Not permitted</div>')

	def on_cancel_after_draft(self):
		validate_workflow_states(self)
		notify_workflow_states(self)

	def on_cancel(self):
		if self.travel_claim:
			frappe.throw("Cancel the Travel Claim before cancelling Authorization")
		#if not self.cancellation_reason:
		#	frappe.throw("Cancellation Reason is Mandatory when Cancelling Travel Authorization")
		self.cancel_attendance()	
		notify_workflow_states(self)

	def on_update_after_submit(self):
		if self.travel_claim:
			frappe.throw("Cannot change once claim is created")
		self.validate_travel_dates()
		self.check_double_dates()
		#self.assign_end_date()
		self.db_set("end_date_auth", self.items[len(self.items) - 1].date)
		self.cancel_attendance()
		self.create_attendance()

	def set_travel_period(self):
		period = frappe.db.sql("""select min(`date`) as min_date, max(till_date) as max_date
				from `tabTravel Authorization Item` where parent = '{}' """.format(self.name), as_dict=True)
		if period:
			self.from_date 	= period[0].min_date
			self.to_date 	= period[0].max_date

	def create_attendance(self):
		d = getdate(self.items[0].date)
		if self.items[len(self.items) - 1].halt and self.items[len(self.items) - 1].till_date:
			e = getdate(self.items[len(self.items) - 1].till_date)
		else:
			e = getdate(self.items[len(self.items) - 1].date)
		days = date_diff(e, d) + 1
		for a in (d + timedelta(n) for n in range(days)):
			al = frappe.db.sql("select name from tabAttendance where docstatus = 1 and employee = %s and attendance_date = %s", (self.employee, a), as_dict=True)
			if al:
				doc = frappe.get_doc("Attendance", al[0].name)
				doc.cancel()
			#create attendance
			attendance = frappe.new_doc("Attendance")
			attendance.flags.ignore_permissions = 1
			attendance.employee = self.employee
			attendance.employee_name = self.employee_name 
			attendance.attendance_date = a
			attendance.status = "Tour"
			attendance.branch = self.branch
			attendance.company = frappe.db.get_value("Employee", self.employee, "company")
			attendance.reference_name = self.name
			attendance.submit()

	def cancel_attendance(self):
		frappe.db.sql("delete from tabAttendance where reference_name = %s", (self.name))
	
	def assign_end_date(self):
		if self.items:
			self.end_date_auth = self.items[len(self.items) - 1].date 

	##
	# check advance and make necessary journal entry
	##
	def check_advance(self):
		if self.need_advance:
			if self.currency and flt(self.advance_amount_nu) > 0:
				cost_center = frappe.db.get_value("Employee", self.employee, "cost_center")
				advance_account = frappe.db.get_single_value("HR Accounts Settings", "employee_advance_travel")
				expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
				if not cost_center:
					frappe.throw("Setup Cost Center for employee in Employee Information")
				if not expense_bank_account:
					frappe.throw("Setup Default Expense Bank Account for your Branch")
				if not advance_account:
					frappe.throw("Setup Advance to Employee (Travel) in HR Accounts Settings")

				je = frappe.new_doc("Journal Entry")
				je.flags.ignore_permissions = 1 
				je.title = "TA Advance (" + self.employee_name + "  " + self.name + ")"
				je.voucher_type = 'Bank Entry'
				je.naming_series = 'Bank Payment Voucher'
				je.remark = 'Advance Payment against Travel Authorization: ' + self.name;
				je.posting_date = self.posting_date
				je.branch = self.branch
	
				je.append("accounts", {
					"account": advance_account,
					"party_type": "Employee",
					"party": self.employee,
					"reference_type": "Travel Authorization",
					"reference_name": self.name,
					"cost_center": cost_center,
					"debit_in_account_currency": flt(self.advance_amount_nu),
					"debit": flt(self.advance_amount_nu),
					"business_activity": self.business_activity,
					"is_advance": "Yes"
				})

				je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": cost_center,
					"business_activity": self.business_activity,
					"credit_in_account_currency": flt(self.advance_amount_nu),
					"credit": flt(self.advance_amount_nu),
				})
				
				je.insert(ignore_permissions=True)
				
				#Set a reference to the advance journal entry
				self.db_set("advance_journal", je.name)
	
	##
	# Allow only approved authorizations to be submitted
	##
	def check_status(self):
		if self.document_status == "Rejected":
			frappe.throw("Rejected Documents cannot be submitted")
		return
		if not self.document_status == "Approved":
			frappe.throw("Only Approved Documents can be submitted")
			
	##
	#Ensure the dates are consistent
	##
	def validate_travel_dates(self):
		for idx, item in enumerate(self.get("items")):
			if item.halt:
				if not item.till_date:
						frappe.throw(_("Row#{0} : Till Date is Mandatory for Halt Days.").format(item.idx),title="Invalid Date")
			else:
				if not item.till_date:
						item.till_date = item.date

			if idx:
				if item.date != add_days(self.items[idx-1].till_date, 1):
						frappe.throw(_("<b>From Date</b> {0} on line {1} might be wrongly typed. It should have been {2}. Kindly check and submit again").format(item.date, item.idx, add_days(self.items[idx-1].till_date, 1)), title="Invalid Date")
								

	##
	# Allow only the approver to submit the document
	##
	#def validate_submitter(self):
	#	if self.supervisor != frappe.session.user:
	#		frappe.throw("Only the selected supervisor can submit this document")


	##
	# Send notification to the supervisor / employee
	##
	def sendmail(self, to_email, subject, message):
		email = frappe.db.get_value("Employee", to_email, "user_id")
		if email:
			try:
				frappe.sendmail(recipients=email, sender=None, subject=subject, message=message)
			except:
				pass

	def set_dsa_rate(self):
		if self.grade:
			self.db_set("dsa_per_day", frappe.db.get_value("Employee Grade", self.grade, "dsa"))

	def check_double_dates(self):
		if self.items:
			start_date = self.items[0].date
			end_date = self.items[len(self.items) - 1].till_date
			if not end_date:
				end_date = self.items[len(self.items) - 1].date

			tas = frappe.db.sql("""
								select a.name
								from `tabTravel Authorization` a, `tabTravel Authorization Item` b
								where a.employee = %s
								and a.name != %s
								and a.docstatus = 1
								and a.name = b.parent
								and (b.date between %s and %s or %s between b.date and b.till_date or %s between b.date and b.till_date)
								""", (str(self.employee), str(self.name), str(start_date), str(end_date), str(start_date), str(end_date)), as_dict=True)
			if tas:
				frappe.throw("The dates in your current Travel Authorization has already been claimed in " + str(tas[0].name))
				
			las = frappe.db.sql("select name from `tabLeave Application` where docstatus = 1 and employee = %s and (from_date between %s and %s or to_date between %s and %s)", (str(self.employee), str(start_date), str(end_date), str(start_date), str(end_date)), as_dict=True)					
			if las:
				frappe.throw("The dates in your current travel authorization has been used in leave application " + str(las[0].name))

@frappe.whitelist()
def make_travel_claim(source_name, target_doc=None): 
	def update_date(obj, target, source_parent):
		target.posting_date = nowdate()
		target.supervisor = None
	
	def transfer_currency(obj, target, source_parent):
		if obj.halt:
			target.from_place = None
			target.to_place = None
		else:
			target.no_days = 1
			target.halt_at = None
		target.currency = source_parent.currency
		target.dsa = source_parent.dsa_per_day
		if target.currency == "BTN":
				target.exchange_rate = 1
		else:
				target.exchange_rate = get_exchange_rate(target.currency, "BTN")
		target.amount = target.dsa
		if target.halt:
			target.amount = flt(target.dsa) * flt(target.no_days)
		target.actual_amount = target.amount * target.exchange_rate

	def adjust_last_date(source, target):
		dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
		percent = flt(dsa_percent) / 100.0
		target.items[len(target.items) - 1].dsa_percent = dsa_percent
		target.items[len(target.items) - 1].actual_amount = target.items[len(target.items) - 1].actual_amount * percent
		target.items[len(target.items) - 1].amount = target.items[len(target.items) - 1].amount * percent
		target.items[len(target.items) - 1].last_day = 1 

	doc = get_mapped_doc("Travel Authorization", source_name, {
			"Travel Authorization": {
				"doctype": "Travel Claim",
				"field_map": {
					"name": "ta",
					"posting_date": "ta_date",
					"advance_amount_nu": "advance_amount"
				},
				"postprocess": update_date,
				"validation": {"docstatus": ["=", 1]}
			},
			"Travel Authorization Item": {
				"doctype": "Travel Claim Item",
				"postprocess": transfer_currency,
				"travel_authorization": "parent"
			},
		}, target_doc, adjust_last_date)
	return doc

@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency):
	# Following line is replaced by subsequent code by SHIV on 2020/09/22
	#ex_rate = frappe.db.get_value("Currency Exchange", {"from_currency": from_currency, "to_currency": to_currency}, "exchange_rate")
	ex_rate = frappe.db.sql("""select exchange_rate 
					from `tabCurrency Exchange`
					where from_currency = '{from_currency}'
					and to_currency = '{to_currency}'
					and `date` <= now()
					order by `date` desc
					limit 1
	""".format(from_currency=from_currency, to_currency=to_currency), as_dict=False)
	if not ex_rate:
		frappe.throw("No Exchange Rate defined in Currency Exchange! Kindly contact your accounts section")
	else:
		return ex_rate[0][0]

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabTravel Authorization`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabTravel Authorization`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabTravel Authorization`.supervisor = '{user}' and `tabTravel Authorization`.workflow_state != 'Draft')
	)""".format(user=user)

