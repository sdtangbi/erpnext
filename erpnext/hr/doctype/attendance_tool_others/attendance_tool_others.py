# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document


class AttendanceToolOthers(Document):
	pass


@frappe.whitelist()
def get_employees(date, employee_type, cost_center, branch, unit):
	attendance_not_marked = []
	attendance_marked = []
	employee_list = frappe.get_list(employee_type, fields=["name", "person_name"], filters={
		"status": "Active", "cost_center": cost_center, "branch": branch, "unit": unit}, order_by="person_name")
	marked_employee = {}
	for emp in frappe.get_list("Attendance Others", fields=["employee", "status"],
							   filters={"date": date}):
		marked_employee[emp['employee']] = emp['status']

	for employee in employee_list:
		employee['status'] = marked_employee.get(employee['name'])
		if employee['name'] not in marked_employee:
			attendance_not_marked.append(employee)
		else:
			attendance_marked.append(employee)
	return {
		"marked": attendance_marked,
		"unmarked": attendance_not_marked
	}


@frappe.whitelist()
def mark_employee_attendance(employee_list, status, date, employee_type, cost_center, branch, unit):
	employee_list = json.loads(employee_list)
	for employee in employee_list:
		attendance = frappe.new_doc("Attendance Others")
		attendance.employee_type = employee_type
		attendance.employee = employee['name']
		attendance.date = date
		attendance.cost_center = cost_center
		attendance.branch = branch
		attendance.unit = unit
		attendance.status = status
		attendance.submit()
