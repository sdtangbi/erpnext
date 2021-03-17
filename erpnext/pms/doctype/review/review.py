# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.model.document import Document


class Review(Document):
    def validate(self):
        self.check_duplicate_entry()
    
    def on_submit(self):
        self.validate_calendar()

    def validate_calendar(self):
        # check whether pms is active for target setup
        if not frappe.db.exists("PMS Calendar",{"name": self.pms_calendar,"docstatus": 1,
                    "review_start_date":("<",self.date),"review_end_date":(">",self.date)}):
            frappe.throw(_('<b>Review for PMS Calendar {} is not open</b>').format(self.pms_calendar))

    def check_duplicate_entry(self):
        # check duplicate entry for particular employee
        if frappe.db.exists("Review", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
            frappe.throw(_('<b>You have already reviewed the current Fiscal Year PMS</b>'))

    def get_target(self):
        # get Target
        data = frappe.db.sql("""
			SELECT 
				pte.performance_target
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
            frappe.throw(_('There are no Target defined for Your ID <b>{}</b>'.format(self.employee)))
        # set Target Performance
        self.set('review_target_item', [])
        for d in data:
            row = self.append('review_target_item', {})
            row.review_performance_target = d.performance_target
            row.update(d)
        return

    def get_competency(self):
        data = frappe.db.sql("""
			SELECT 
				pte.competency
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
            frappe.throw(_('There are no Competency defined for your ID <b>{}</b>'.format(self.employee)))

        self.set('review_competency_item', [])
        for d in data:
            row = self.append('review_competency_item', {})
            row.competency = d.competency
            row.update(d)
        return
