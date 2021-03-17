# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FeedbackSetting(Document):
	def validate(self):
		pass

	def before_submit(self):
		if frappe.db.exists("Feedback Setting", {"docstatus":1, "status":"Open"}):
			feedbackID, feedbackTitle = frappe.db.get_value("Feedback Setting", {"docstatus":1, "status":"Open"}, ['name',"title"])
			frappe.throw("To activate this feedback collection, first close the active feedback : {} ({})".format(feedbackTitle, feedbackID))	

	def on_update_after_submit(self):
		count = 0
		for a in frappe.db.sql("select name, title from `tabFeedback Setting` where status = 'Open' and docstatus = 1 and name != '{0}'".format(self.name), as_dict=True):
			frappe.throw("To activate this feedback collection, first close the active feedback : {0} ({1})".format(a.title, a.name))	