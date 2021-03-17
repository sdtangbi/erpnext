# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class TargetSetUp(Document):

    def validate(self):
        self.check_target()
        self.check_duplicate_entry()

    def on_submit(self):
        self.validate_calendar()

    def validate_calendar(self):
        # check whether pms is active for target setup
        if not frappe.db.exists("PMS Calendar",{"name": self.pms_calendar,"docstatus": 1,
                    "target_start_date":("<",self.date),"target_end_date":(">",self.date)}):
            frappe.throw(_('<b>Target Set Up for PMS Calendar {} is not open</b>').format(self.pms_calendar))

    def check_duplicate_entry(self):
        # check duplicate entry for particular employee
        if frappe.db.exists("Target Set Up", {'employee': self.employee, 'pms_calendar': self.pms_calendar, 'docstatus': 1}):
            frappe.throw(_('<b>You have already set the Target for the current Fiscal Year</b>'))

    def check_target(self):
        # validate target
        if frappe.db.exists("PMS Group",{"group_name":self.pms_group,"required_to_set_target":1}):
            if not self.target_item:
                frappe.throw(_('You need to <b>Set The Target</b>'))
            total_target_weightage = 0
            # total weightage must be 100
            for i, t in enumerate(self.target_item):
                if t.quality < 0 or t.quantity < 0 or t.weightage < 0 :
                    frappe.throw(_("Negative value is not allowed in Target Item at Row {}".format(i+1)))
                total_target_weightage += flt(t.weightage)

            if total_target_weightage != 100:
                frappe.throw(_('<b>Sum of Weightage in Target Item must be 100</b>'))

        if not self.competency:
            frappe.throw(_('Competency cannot be empty'))

    def get_competency(self):
        # fetch employee category based on employee designation
        employee_category = frappe.db.sql("""
				SELECT 
					ec.employee_category 
				FROM 
					`tabEmployee Category` ec 
				INNER JOIN 
					`tabEmployee Category Group` ecg
				ON 
					ec.name = ecg.parent 
				WHERE 
					ecg.designation = '{}'
		""".format(self.designation), as_dict=True)
        if not employee_category:
            frappe.throw(
                _('Your designation <b>{0}</b> is not defined in the Employee Category'.format(self.designation)))

        # get competency applicable to particular category
        data = frappe.db.sql("""
			SELECT 
				wc.competency,wc.weightage
			FROM 
				`tabWork Competency` wc 
			INNER JOIN
				`tabWork Competency Item` wci 
			ON 
				wc.name = wci.parent 
			WHERE	
				wci.applicable = 1 
			AND 
				wci.employee_category = '{0}' 
            ORDER BY 
                wc.competency
		""".format(employee_category[0].employee_category), as_dict=True)

        if not data:
            frappe.throw(_('There are no Work Competency defined'))
        # set competency item values
        self.set('competency', [])
        for d in data:
            row = self.append('competency', {})
            row.update(d)
        return
