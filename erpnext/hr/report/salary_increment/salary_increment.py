# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
        columns = get_columns()
        data = get_data(filters)

        return columns, data
    
def get_columns():
        return [
                ("Branch ") + ":Link/Branch:200",
                ("Employee ID") + ":Link/Employee:100",
                ("Employee Name") + ":Data:150",
                ("Designation") + ":Data:150",
                ("Grade") + ":Data:80",
                ("Date Of Joining") + ":Data:100",
		("Year") + ":Data:80",
                ("Month")+ ":Data:50",
                ("Current Basic") + ":Currency:120",
                ("Increment") + ":Currency:80",
                ("New Basic") + ":Currency:120",
                ("Payscale Minimum") + "::150",
                ("Payscale Increment") + "::150",
                ("Payscale Maximum") + "::150",
                ("Payscale_Format") + "::150",
                ("Division") + ":Data:150",
                ("Remarks") + ":Data:150"
        ]
        #########Payscale Minimum, Payscale Increment, Payscale Maximum and Payscale Format added by Cheten on 7/09/2020################
def get_data(filters):
	#docstatus = ""
        if filters.uinput == "Draft":
                docstatus = 0
        if filters.uinput == "Submitted":
                docstatus = 1
        if filters.uinput == "All":
                docstatus = "si.docstatus"
        query =  """SELECT 
                        si.branch, 
                        si.employee, 
                        si.employee_name,
                        e.designation, 
                        si.grade, 
                        e.date_of_joining,
                        si.fiscal_year, 
                        si.month,
                        si.old_basic, 
                        si.increment, 
                        si.new_basic, 
                        si.payscale_minimum,
                        si.payscale_increment,
                        si.payscale_maximum,
                        CONCAT_WS('-', round(si.payscale_minimum,2), round(si.payscale_increment,2), round(si.payscale_maximum,2))as Payscale_Format,
                        si.division, 
                        si.remarks
                    FROM `tabSalary Increment` si, `tabEmployee` e
                    WHERE si.docstatus = {0}
                    AND e.name = si.employee
                """.format(docstatus) 
        if filters.get("fiscal_year"):
                query += " and fiscal_year = \'"+ str(filters.fiscal_year) + "\'"
        if filters.get("increment_and_promotion_cycle"):
                # month = {'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06',
                #          'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12'}
                # query += " and month = \'"+ str(month[filters.increment_and_promotion_cycle]) + "\'"
                query += " and month = \'"+ filters.increment_and_promotion_cycle + "\'"
        if filters.get("branch"):
                query += " and branch = \'"+ str(filters.branch) + "\'"
        
        #frappe.msgprint(docstatus)
        query += "order by branch"
        return frappe.db.sql(query)
      
