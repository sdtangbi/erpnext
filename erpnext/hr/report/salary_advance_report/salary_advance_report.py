# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cstr
from frappe import msgprint, _


def execute(filters=None):
	if not filters: 
		filters = {}
	data    = []
	columns = []

	data = get_data(filters)
	if not data:
		return columns, data

	columns = get_columns(data)

	return columns, data

def get_columns(data):
	columns = [
		_("Employee") + ":Link/Employee:120", _("Employee Name") + "::140", _("Designation") + ":Link/Designation:120",
		_("Branch") + ":Link/Branch:120", _("Date") + ":Data:80", _("Advance Amount") + ":Currency:120", 
		_("No Of Installments") + ":Data:80", _("Monthly Deduction") + ":Currency:120", 
		_("Recovered Amount") + ":Currency:120", _("Balance") + ":Currency:120"
	]

	return columns

def get_data(filters):
	conditions, filters = get_conditions(filters)

	data = frappe.db.sql("""
		select x.*, ifnull(x.total_claim,0) - ifnull(x.total_collected,0) as balance
		from (
			select 
				sa.employee, sa.employee_name, sa.designation, 
				sa.branch, sa.application_date, sa.total_claim, sa.deduction_month, sa.monthly_deduction,
				(select sum(sd.amount)
				from `tabSalary Detail` sd
				where sd.reference_number = sa.name
				and sd.docstatus = 1
				) total_collected
			from `tabSalary Advance` sa
			where sa.docstatus = 1 %s
		) x
		""" % conditions, filters)

	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and sa.application_date between %(from_date)s and %(to_date)s"

	if filters.get("branch"): conditions += " and sa.branch = %(branch)s"
	if filters.get("employee"): conditions += " and sa.employee = %(employee)s"


	return conditions, filters
