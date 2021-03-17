# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, get_datetime, get_url, nowdate, now_datetime

class Branch(Document):
        def validate(self):
                self.validate_amounts()
                self.update_gis_policy_no()
                self.check_duplicates()

        def validate_amounts(self):
                for i in self.items:
                        if flt(i.imprest_limit) < 0:
                                frappe.throw(_("Row#{0} : Imprest limit cannot be less than zero.").format(i.idx),title="Invalid Data")
                                
        def update_gis_policy_no(self):
                # Following code commented due to performance issue
                '''
                prev_doc = frappe.get_doc(self.doctype, self.name)
                if prev_doc.gis_policy_number != self.gis_policy_number:
                        for e in frappe.get_all("Employee",["name"],{"branch": self.name}):
                             emp = frappe.get_doc("Employee",e.name)
                             emp.update({"gis_policy_number": self.gis_policy_number})
                             emp.save(ignore_permissions = True)
                '''

                
                #prev_doc = frappe.get_doc(self.doctype, self.name)
                #if prev_doc.gis_policy_number != self.gis_policy_number:
                if self.get_db_value("gis_policy_number") != self.gis_policy_number:
                        frappe.db.sql("""
                                update `tabEmployee`
                                set gis_policy_number = '{1}'
                                where branch = '{0}'
                        """.format(self.name, self.gis_policy_number))

        def check_duplicates(self):
                dup = {}
                # Checking for duplicates in imprest settings
                for i in self.items:
                        if i.imprest_type in dup:
                                frappe.throw(_("Duplicate values found for Imprest Type <b>`{0}`</b>").format(i.imprest_type),title="Duplicate Values")
                        else:
                                dup.update({i.imprest_type: 1})
                                if i.default:
                                        if 'default' in dup:
                                                dup.update({'duplicate': 1})
                                                
                                        dup.update({'default': 1})

                # Checking for duplicate defaults in imprest settings
                if 'duplicate' in dup:
                        frappe.throw(_("Only one imprest type can be default."),title="Duplicate Values")
                        

