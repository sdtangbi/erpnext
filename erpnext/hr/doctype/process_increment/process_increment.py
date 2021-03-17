# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate
from frappe import _
from erpnext.hr.hr_custom_functions import get_month_details
import calendar

class ProcessIncrement(Document):
	def get_emp_list(self, process_type=None):
		cond = self.get_filter_condition()

		if process_type == "create":
			cond += self.get_joining_releiving_condition()
			emp_list = frappe.db.sql("""
				select t1.name
				  from `tabEmployee` as t1
				 where t1.status = 'Active'
				   and t1.increment_cycle = '{0}'
				   and not exists(select 1
						   from `tabSalary Increment` as t3
						   where t3.employee = t1.employee
						   and t3.docstatus != 2
						   and t3.fiscal_year = '{1}'
						   and t3.month = '{2}')
				   {3}
				 order by t1.branch, t1.name
			""".format(calendar.month_name[int(self.month)],self.fiscal_year,self.month,cond),as_dict=True)
		else:
			emp_list = frappe.db.sql("""
				select t1.name
				from `tabSalary Increment` as t1
				where t1.fiscal_year = '{0}'
				and t1.month = '{1}'
				and t1.docstatus = 0
				{2}
				order by t1.branch, t1.name
			""".format(self.fiscal_year, self.month, cond), as_dict=True)
		
		return emp_list

	def get_filter_condition(self):
		self.check_mandatory()

		cond = ''
		for f in ['company', 'branch', 'department', 'division', 'designation', 'employee']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"

		return cond

	def check_mandatory(self):
		for f in ['company', 'month', 'fiscal_year']:
			if not self.get(f):
				frappe.throw(_("Please set {0}").format(f))

	def get_joining_releiving_condition(self):
		m = get_month_details(self.fiscal_year, self.month)

		cond = """
			and ifnull(t1.date_of_joining, '%(month_end_date)s') <= '%(month_end_date)s'
			and ifnull(t1.relieving_date, '%(month_start_date)s') >= '%(month_start_date)s'
		""" % m
		return cond

	def process_increment(self, process_type=None, name=None):
		self.check_permission('write')
		msg = ""
		
		if name:
			try:
				if process_type == "create":
					si = frappe.new_doc("Salary Increment")
					si.employee = name
					si.fiscal_year = self.fiscal_year
					si.month = self.month
					si.get_employee_payscale()
					si.save(ignore_permissions = True)

					msg = "Created Successfully"
				else:
					if process_type == "remove":
						si = frappe.get_doc("Salary Increment", name)
						si_list = frappe.db.sql("delete from `tabSalary Increment` where name='{0}'".format(name))
						frappe.db.commit()
						msg = "Removed Successfully"
					else:
						si = frappe.get_doc("Salary Increment", name)
						si.submit()
						msg = "Submitted Successfully"
				if si:
					format_string = 'href="#Form/Salary Increment/{0}"'.format(si.name)
					return '<tr><td><a {0}>{1}</a></td><td><a {0}>{2}</a></td><td>{3}</td><td>{4}</td></tr>'.format(format_string, si.name, si.employee_name, msg, si.branch)
			except Exception as e:
				return '<div style="color:red;">Error: {0}</div>'.format(str(e))

		return name

	def create_increment(self):
		"""
			Creates salary increment for selected employees if already not created
		"""

		emp_list = self.get_emp_list()
		si_list = []
		for emp in emp_list:
			if not frappe.db.sql("""select name from `tabSalary Increment`
					where docstatus!= 2 and employee = %s and month = %s and fiscal_year = %s and company = %s
					""", (emp.name, self.month, self.fiscal_year, self.company)) and flt(emp.no_of_months) >= 3:
				payscale = get_employee_payscale(emp.name, emp.employee_subgroup, self.fiscal_year, self.month)

				# Prorate based on noof months
				minimum_months       = 3
				total_months         = flt(emp.no_of_months)
				calculated_factor    = 1 if flt(total_months)/12 >= 1 else round(flt(total_months)/12,2)
				calculated_increment = round(flt(payscale.increment)*flt(calculated_factor))
				
				if payscale:
					si = frappe.get_doc({
						"doctype": "Salary Increment",
						"fiscal_year": self.fiscal_year,
						"employee": emp.name,
						"month": self.month,
						"company": emp.company,
						"branch": emp.branch,
						"department": emp.department,
						"division": emp.division,
						"section": emp.section,
						"employee_subgroup": emp.employee_subgroup,
						"payscale_minimum": payscale.minimum,
						"payscale_increment": payscale.increment,
						"payscale_maximum": payscale.maximum,
						"old_basic": payscale.old_basic,
						"new_basic": flt(payscale.old_basic)+flt(calculated_increment),
						"increment": calculated_increment,
						"employee_name": emp.employee_name,
						"salary_structure": payscale.salary_structure,
						"minimum_months": minimum_months,
						"total_months": total_months,
						"calculated_factor": calculated_factor,
						"calculated_increment": calculated_increment,
						"date_of_reference": emp.date_of_joining
					})
					si.insert()
					si_list.append(si.name)

		return self.create_log(si_list)

	def remove_increment(self):
		cond = ''
		for f in ['company', 'branch', 'department', 'division', 'designation', 'employee']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"

		si_list = frappe.db.sql_list("""
				select t1.name from `tabSalary Increment` as t1
				where t1.fiscal_year = '%s'
				and t1.month = '%s'
				and t1.docstatus = 0
				%s
				""" % (self.fiscal_year, self.month, cond))
		si_log = []
		if si_list:
			for row in si_list:
				frappe.delete_doc("Salary Increment", frappe.db.sql_list("""
					select t1.name from `tabSalary Increment` as t1
					where t1.name = '%s'
					""" % row), for_reload=True)
				si_log.append(row)

		return self.remove_log(si_log)
	
	def submit_increment(self):
		"""
			Submit all salary increments based on selected criteria
		"""
		cond = ''
		for f in ['company', 'branch', 'department', 'division', 'designation', 'employee']:
			if self.get(f):
				cond += " and t1." + f + " = '" + self.get(f).replace("'", "\'") + "'"

		si_list = frappe.db.sql_list("""
				select t1.name from `tabSalary Increment` as t1
				where t1.fiscal_year = '%s'
				and t1.month = '%s'
				and t1.docstatus = 0
				%s
				""" % (self.fiscal_year, self.month, cond))
		si_log = []
		not_submitted_si = []
		
		for row in si_list:
			si_obj = frappe.get_doc("Salary Increment",row)
			try:
				si_log.append(row)
				si_obj.submit()
			except Exception as e:
				not_submitted_si.append(row)
				frappe.msgprint(e)
				continue

		return self.submit_log(si_log, not_submitted_si)

	def create_log(self, si_list):
		log = "<p>" + _("No employee for the above selected criteria OR salary increment already created") + "</p>"
		if si_list:
			log = "<b>" + _("Salary Increment Created") + "</b>\
			<br><br>%s" % '<br>'.join(self.format_as_links(si_list))
		return log

	def remove_log(self, si_list):
		log = "<p>" + _("No Records found for the above selected criteria OR salary increment already removed") + "</p>"
		if si_list:
			log = "<b>" + _("Salary Increment Removed") + "</b>\
			<br><br>%s" % '<br>'.join(si_list)
		return log        

	def submit_log(self, si_list, not_submitted_si):
		log = "<p>" + _("No Records found for the above selected criteria OR salary increment already submitted") + "</p>"
		if si_list:
			log = "<b>" + _("Salary Increment Submitted")
			log += "</b><br><br>%s" % '<br>'.join(self.format_as_links(si_list))
		if not_submitted_si:
			log += "<br>%s" % '<br>'.join(self.format_as_links(not_submitted_si))
			
		return log
	
	def format_as_links(self, si_list):
		return ['<a href="#Form/Salary Increment/{0}">{0}</a>'.format(s) for s in si_list]

