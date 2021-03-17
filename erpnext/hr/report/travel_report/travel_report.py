#Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_columns(filters):
	cols = [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee Name") + ":Data:120",
				_("TC Name") + ":Link/Travel Claim:120",
		_("Designation") + ":Data:120",
				_("Cost Center") + ":Data:160",
				_("Department") + ":Data:160",
				_("From") + ":Date:90",
				_("To Date") + ":Date:90",
		_("No Of Days") + ":Int:80",
		_("Place Type") + ":Data:100",
		_("Month") + ":Data:80",
		_("Dsa Per Day") + ":Currency:100",
		_("Total Claim") + ":Currency:120"
	]
	return cols


def get_data(filters):
	query ="""
		select 
		tc.employee,
		tc.employee_name, 
		tc.name, 
		e.designation, 
		e.cost_center,
		tc.department, 
		min(tci.date), 
		max((case when tci.halt = 1 then tci.till_date when tci.halt = 0 then tci.date end)) as to_date,
		sum(tci.no_days), 
		tc.place_type, 
		date_format(tc.posting_date,'%M'), 
		tc.dsa_per_day, 
		tc.total_claim_amount  
		from `tabTravel Claim` tc, `tabEmployee` e, `tabTravel Claim Item` tci 
		where tci.parent = tc.name and e.name = tc.employee
				and tc.docstatus = 1
		"""
	if filters.get("employee"):
		query += " and tc.employee = \'" + str(filters.employee) + "\'"

	if filters.get("from_date") and filters.get("to_date"):
  		query += " and tc.posting_date between  '{0}' and '{1}'".format(filters.get("from_date"), filters.get("to_date"))
	if filters.get("fiscal_year"):
		query += " and year(tc.posting_date) = {0}".format(filters.get("fiscal_year"))

	if filters.get("cost_center"):
		query += " and e.cost_center = \'" + str(filters.cost_center) + "\'"
	query += " group by tc.name, tc.employee, e.designation, tc.department"
	#frappe.msgprint("This Report is UnderDeveloped")
	return frappe.db.sql(query)
