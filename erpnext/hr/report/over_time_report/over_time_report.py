# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, cint, getdate
from frappe import msgprint, _
from calendar import monthrange
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee

def execute(filters=None):
	validate_filters(filters)
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def validate_filters(filters):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

def get_data(filters):

	query = "select a.employee as employee, a.employee_name as employee_name,c.designation as designation,c.grade as grade, a.rate as rate, \
		sum(b.number_of_hours) as hours,sum(round(b.number_of_hours*a.rate,2)) as amount, \
		c.cost_center from `tabOvertime Application Item` as b inner join `tabOvertime Application` as a  on b.parent = a.name \
		inner join `tabEmployee` as c on a.employee=c.employee \
		where a.docstatus=1 and b.date between  \'"+str(filters.from_date)+"\' and \'"+str(filters.to_date)+"\' "

	if filters.cost_center:
		query+=" and c.cost_center = \'"+filters.cost_center+"\'"

	if filters.employee:
		query+=" and a.employee = \'"+filters.employee+"\'"

	if filters.designation:
		query+=" and c.designation = \'"+filters.designation+"\'"

	if filters.grade:
		query+=" and c.grade = \'"+filters.grade+"\'"
	
	query+=" group by a.employee order by a.employee"

	data = frappe.db.sql(query, as_dict=True)
	
	return data

def get_columns():
	return [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "designation",
			"label": _("Designation"),
			"fieldtype": "Link",
			"options": "Designation",
			"width": 130
		},
		{
			"fieldname": "grade",
			"label": _("Grade"),
			"fieldtype": "Link",
			"options": "Employee Grade",
			"width": 120
		},
		{
			"fieldname": "rate",
			"label": _("Hourly Rate"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname" : "hours",
			"label": _("Total Hours"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname" : "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "cost_center",
			"label": _("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 400
		},
	]
	
	return columns
