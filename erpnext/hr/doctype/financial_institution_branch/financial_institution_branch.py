# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FinancialInstitutionBranch(Document):
	def autoname(self):
		self.name = " - ".join([self.branch_name,str(self.financial_institution).strip()])

