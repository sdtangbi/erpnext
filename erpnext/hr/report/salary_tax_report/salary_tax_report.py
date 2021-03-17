# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
'''
--------------------------------------------------------------------------------------------------------------------------
Version          Author          CreatedOn          ModifiedOn          Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		  SSK		 07/09/2016                           Report created
--------------------------------------------------------------------------------------------------------------------------                                                                          
'''

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cstr
from frappe import msgprint, _

def execute(filters=None):
	if not filters: 
		filters = {}

	data = get_data(filters)
	columns = get_columns(data)
	
	return columns, data
	
def get_columns(data):
	columns = [
		_("Title") + ":Link/Salary Tax:320", _("From Date") + ":Date:80", _("To Date") + ":Date:80",
		_("Lower Limit") + ":Float:120", _("Tax") + ":Float:120", _("Upper Limit") + ":Float:120"
	]
	
	return columns
	
def get_data(filters):
	conditions, filters = get_conditions(filters)
	conditions2 = get_conditions2(filters)
	
	data = frappe.db.sql("""
		select t1.name, t1.from_date, t1.to_date, t2.lower_limit, t2.tax, t2.upper_limit
		from `tabSalary Tax` t1, `tabSalary Tax Item` t2
		where t2.parent = t1.name %s
		order by t2.lower_limit
		""" % conditions, filters)

	if data:
		pass
	else:
		if filters.get("from_date") > filters.get("to_date"):
			frappe.throw(_("Please select a valid date range."))
			
		max_limit = frappe.db.sql("""
			select max(t2.upper_limit)
			from `tabSalary Tax` t1, `tabSalary Tax Item` t2
			where t2.parent = t1.name %s
			""" % conditions2, filters)

		if filters.get("gross_amt") > max_limit[0][0]:
			tax_amt = flt((((flt(filters.get("gross_amt")) if flt(filters.get("gross_amt")) else 0.00)-83333.00)*0.25)+11875.00)

			data = frappe.db.sql("""
				select "Tax Beyond RRCO Slab Details" title,
				%(from_date)s from_date,
				%(to_date)s to_date,
				{0} lower_limit,
				{1} tax,
				%(gross_amt)s upper_limit
				""".format(max_limit[0][0],tax_amt),filters)

	if not data:
		msgprint(_("No Data Found. "), raise_exception=1)
	
	return data
	
def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"): conditions += " and ((t1.from_date between ifnull(%(from_date)s,now()) and ifnull(%(to_date)s,now())) \
		or (ifnull(t1.to_date,now()) between ifnull(%(from_date)s,now()) and ifnull(%(to_date)s,now())))"
	if filters.get("gross_amt"): conditions += " and %(gross_amt)s between t2.lower_limit and t2.upper_limit"
	
	return conditions, filters
	
def get_conditions2(filters):
	conditions = ""
	if filters.get("from_date"): conditions += " and ((t1.from_date between ifnull(%(from_date)s,now()) and ifnull(%(to_date)s,now())) \
		or (ifnull(t1.to_date,now()) between ifnull(%(from_date)s,now()) and ifnull(%(to_date)s,now())))"
	
	return conditions
	
