# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from dateutil.relativedelta import relativedelta
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff, get_last_day
from frappe import _
from erpnext.accounts.utils import get_fiscal_year
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba

class IncrementEntry(Document):
	def onload(self):
		if not self.docstatus==1 or self.salary_increments_submitted:
				return

		# check if salary increments were manually submitted
		entries = frappe.db.count("Salary Increment", {'increment_entry': self.name, 'docstatus': 1}, ['name'])
		if cint(entries) == len(self.employees):
				self.set_onload("submitted_si", True)

	def validate(self):
		self.set_month_dates()

	def on_submit(self):
		self.create_salary_increments()

	def before_submit(self):
		pass

	def on_cancel(self):
		self.remove_salary_increments()

	def get_emp_list(self, process_type=None):
		self.set_month_dates()

		cond = self.get_filter_condition()
		cond += self.get_joining_relieving_condition()

		emp_list = frappe.db.sql("""
			select t1.name as employee, t1.employee_name, t1.department, t1.designation
			from `tabEmployee` t1
			where t1.status = 'Active'
			and t1.increment_cycle = '{}' 
			and not exists(select 1
					from `tabSalary Increment` as t3
					where t3.employee = t1.name
					and t3.docstatus != 2
					and t3.fiscal_year = '{}'
					and t3.month = '{}')
			and exists(select 1
					from `tabSalary Structure` sst
					where sst.employee = t1.name
					and sst.is_active = 'Yes')
			{}
			order by t1.branch, t1.name
		""".format(self.month_name, self.fiscal_year, self.month_name, cond), as_dict=True)

		return emp_list

	def fill_employee_details(self):
		self.set('employees', [])
		employees = self.get_emp_list()
		if not employees:
			frappe.throw(_("No employees for the mentioned criteria"))

		for d in employees:
			self.append('employees', d)

		self.number_of_employees = len(employees)

	def get_filter_condition(self):
		self.check_mandatory()

		cond = ''
		
		for f in ['company', 'branch', 'department', 'designation', 'employee']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"

		return cond

	def get_joining_relieving_condition(self):
		cond = """
			and ifnull(t1.date_of_joining, '0000-00-00') <= '%(end_date)s'
			and ifnull(t1.relieving_date, '2199-12-31') >= '%(start_date)s'
		""" % {"start_date": self.start_date, "end_date": self.end_date}
		return cond

	# following method created by SHIV on 2020/10/20
	def set_month_dates(self):
		months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
		month = str(int(months.index(self.month_name))+1).rjust(2,"0")

		month_start_date = "-".join([str(self.fiscal_year), month, "01"])
		month_end_date   = get_last_day(month_start_date)

		self.start_date = month_start_date
		self.end_date = month_end_date
		self.month = month

	def check_mandatory(self):
		# following line is replaced by subsequent by SHIV on 2020/10/20
		for fieldname in ['company', 'fiscal_year', 'month']:
			if not self.get(fieldname):
				frappe.throw(_("Please set {0}").format(self.meta.get_label(fieldname)))

	def create_salary_increments(self):
		"""
			Creates salary slip for selected employees if already not created
		"""
		self.check_permission('write')
		self.created = 1
		emp_list = [d.employee for d in self.get_emp_list()]

		if emp_list:
			args = frappe._dict({
				"company": self.company,
				"posting_date": self.posting_date,
				"increment_entry": self.name,
				"fiscal_year": self.fiscal_year,
				"month": self.month_name
			})
			if len(emp_list) > 300:
				frappe.enqueue(create_salary_increments_for_employees, timeout=600, employees=emp_list, args=args)
			else:
				create_salary_increments_for_employees(emp_list, args, publish_progress=False)
				# since this method is called via frm.call this doc needs to be updated manually
				self.reload()

	def get_sal_increment_list(self, si_status, as_dict=False):
		"""
			Returns list of salary increments based on selected criteria
		"""
		cond = self.get_filter_condition()

		si_list = frappe.db.sql("""
			select t1.name, t1.salary_structure from `tabSalary Increment` t1
			where t1.docstatus = %s %s
			and t1.increment_entry = %s
		""" % ('%s', cond, '%s'), (si_status, self.name), as_dict=as_dict)
		return si_list

	def remove_salary_increments(self):
		self.check_permission('write')
		si_list = self.get_sal_increment_list(si_status=0)
		if len(si_list) > 300:
			frappe.enqueue(remove_salary_increments_for_employees, timeout=600, increment_entry=self, salary_increments=si_list)
		else:
			remove_salary_increments_for_employees(self, si_list, publish_progress=False)

	def submit_salary_increments(self):
		self.check_permission('write')
		si_list = self.get_sal_increment_list(si_status=0)
		if len(si_list) > 300:
			frappe.enqueue(submit_salary_increments_for_employees, timeout=600, increment_entry=self, salary_increments=si_list)
		else:
			submit_salary_increments_for_employees(self, si_list, publish_progress=False)

	def email_salary_slip(self, submitted_ss):
		if frappe.db.get_single_value("HR Settings", "email_salary_slip_to_employee"):
			for ss in submitted_ss:
				ss.email_salary_slip()

def remove_salary_increments_for_employees(increment_entry, salary_increments, publish_progress=True):
	deleted_si = []
	not_deleted_si = []
	frappe.flags.via_increment_entry = True

	count = 0
	for si in salary_increments:
		try:
			frappe.delete_doc("Salary Increment",si[0])
			deleted_si.append(si[0])
		except frappe.ValidationError:
			not_deleted_si.append(si[0])

		count += 1
		if publish_progress:
			frappe.publish_progress(count*100/len(salary_increments), title = _("Removing Salary Increments..."))
	if deleted_si:
		frappe.msgprint(_("Salary Increments Removed Successfully"))

	if not deleted_si and not not_deleted_si:
		frappe.msgprint(_("No salary increment found to remove for the above selected criteria OR salary increment already submitted"))

	if not_deleted_si:
		frappe.msgprint(_("Could not submit some Salary Increments"))

def create_salary_increments_for_employees(employees, args, publish_progress=True):
	salary_increments_exists_for = get_existing_salary_increments(employees, args)
	count=0
	increment_entry = frappe.get_doc("Increment Entry", args.increment_entry)

	for emp in increment_entry.get("employees"):
		if emp.employee not in salary_increments_exists_for:
			args.update({
				"doctype": "Salary Increment",
				"employee": emp.employee
			})
			si = frappe.get_doc(args)
			si.get_employee_payscale()
			si.insert()
			count+=1

			ied = frappe.get_doc("Increment Employee Detail", emp.name)
			ied.db_set("salary_increment", si.name)
			if publish_progress:
				frappe.publish_progress(count*100/len(set(employees) - set(salary_increments_exists_for)),
					title = _("Creating Salary Increments..."))

	increment_entry.db_set("salary_increments_created", 1)
	increment_entry.notify_update()

def get_existing_salary_increments(employees, args):
	return frappe.db.sql_list("""
		select distinct employee from `tabSalary Increment`
		where docstatus!= 2 and company = %s
			and fiscal_year = %s and month = %s
			and employee in (%s)
	""" % ('%s', '%s', '%s', ', '.join(['%s']*len(employees))),
		[args.company, args.fiscal_year, args.month] + employees)

def submit_salary_increments_for_employees(increment_entry, salary_increments, publish_progress=True):
	submitted_si = []
	not_submitted_si = []
	frappe.flags.via_increment_entry = True

	count = 0
	for si in salary_increments:
		si_obj = frappe.get_doc("Salary Increment",si[0])
		if si_obj.increment<0:
			not_submitted_si.append(si[0])
		else:
			try:
				si_obj.submit()
				submitted_si.append(si_obj)
			except frappe.ValidationError:
				not_submitted_si.append(si[0])

		count += 1
		if publish_progress:
			frappe.publish_progress(count*100/len(salary_increments), title = _("Submitting Salary Increments..."))
	if submitted_si:
		frappe.msgprint(_("Salary Increment submitted for increment cycle {1}, {0}")
			.format(si_obj.fiscal_year, si_obj.month))

		increment_entry.db_set("salary_increments_submitted", 1)
		increment_entry.notify_update()

	if not submitted_si and not not_submitted_si:
		frappe.msgprint(_("No salary increment found to submit for the above selected criteria OR salary increment already submitted"))

	if not_submitted_si:
		frappe.msgprint(_("Could not submit some Salary Increments"))
