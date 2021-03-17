# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Feedback(Document):
	def validate(self):
		self.validate_recipient()
		self.update_emp_detail()		

	def on_submit(self):
		self.add_feedback_log()
		frappe.db.sql("update `tabFeedback` set owner = 'bobl@gmail.com', modified_by = 'bobl@gmail.com' where name ='{0}'".format(self.name))

	def validate_recipient(self):
		doc = frappe.get_doc("Feedback Setting", {"status": "Open", "docstatus":1})
		self.feedback_setting = doc.name
		self.feedback_title = doc.title
		if not self.feedback_setting:
			frappe.throw("Feedback Collection is Close")

		if not frappe.db.exists("Employee", self.recipient):
			frappe.throw("Employee ID {} does not exist in Employee Master".format(self.employee))

		provider_employee_id = frappe.db.get_value("Employee",{"user_id": frappe.session.user}, "name")

		report_to = frappe.db.get_value("Employee", provider_employee_id, "reports_to")
		if report_to != self.recipient:
			if not frappe.db.exists("Feedback Recipient Item", {"parent":provider_employee_id, "employee": self.recipient}):
				frappe.throw("You are not allowed to provide feedback to employee ID {}".format(self.recipient))

		provider_id, provider_name = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["name", "employee_name"])
		
		if frappe.db.exists("Feedback Log", {"feedback_setting":self.feedback_setting, "recipient":self.recipient, "provider":provider_id}):
			frappe.throw("Feedback Already provided for Employee {}, {}".format(self.recipient, self.recipient_name))

	def update_emp_detail(self):
		emp_name, department, branch, designation = frappe.db.get_value("Employee", self.recipient, ["employee_name", "department", "branch", "designation"])
		self.recipient_name = emp_name
		self.department = department
		self.branch = branch
		self.designation = designation

	def add_feedback_log(self):
		provider_id, provider_name = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["name", "employee_name"])
		doc = frappe.new_doc("Feedback Log")
		doc.feedback_setting = self.feedback_setting
		doc.recipient = self.recipient
		doc.recipient_name = self.recipient_name
		doc.provider = provider_id
		doc.provider_name = provider_name
		doc.save(ignore_permissions=True)
