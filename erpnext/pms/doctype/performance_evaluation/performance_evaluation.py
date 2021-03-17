# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PerformanceEvaluation(Document):	
		def get_target(self):
			# get Target
			data = frappe.db.sql("""
				SELECT 
					pte.performance_target,pte.weightage
				FROM 
					`tabTarget Set Up` ts 
				INNER JOIN
					`tabPerformance Target Evaluation` pte
				ON
					ts.name = pte.parent			
				WHERE			
					ts.employee = '{}' and ts.docstatus = 1
				AND 
                    ts.pms_calendar = '{}'
			""".format(self.employee,self.pms_calendar), as_dict=True)

			if not data:
				frappe.throw('There are no Target Performance defined')
			# set Target Performance
			self.set('evaluate_target_item', [])
			for d in data:
				row = self.append('evaluate_target_item', {})
				row.target = d.performance_target
				row.evaluate_target_weightage = d.weightage
				row.update(d)
			return

		def get_competency(self):
			data = frappe.db.sql("""
				SELECT 
					pte.competency,pte.weightage
				FROM 
					`tabTarget Set Up` ts 
				INNER JOIN
					`tabCompetency Item` pte
				ON
					ts.name = pte.parent 		
				WHERE			
					ts.employee = '{}' and ts.docstatus = 1 
				AND 
					ts.pms_calendar = '{}' 
				ORDER BY 
					pte.competency
			""".format(self.employee,self.pms_calendar), as_dict=True)
			if not data:
				frappe.throw('There are no Competency defined')

			self.set('evaluate_competency_item', [])
			for d in data:
				row = self.append('evaluate_competency_item', {})
				row.evaluate_work_competency = d.competency
				row.evaluate_comp_weightage = d.weightage
				row.update(d)
			return

