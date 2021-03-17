# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cstr, add_days, date_diff, nowdate
from frappe import _
from frappe.utils.csvutils import UnicodeWriter
from frappe.model.document import Document
from erpnext.hr.hr_custom_functions import get_salary_tax, get_payroll_settings 

class UploadSalaryStructure(Document):
	pass

@frappe.whitelist()
def get_template():
	if not frappe.has_permission("Salary Structure", "create"):
		raise frappe.PermissionError

	args = frappe.local.form_dict

	w = UnicodeWriter()
	w = add_header(w)

	# write out response as a type csv
	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Salary Structure"

def add_header(w):
	w.writerow(["Notes:"])
	w.writerow(["Please DO NOT change the template headings"])
	w.writerow([""])
	#w.writerow(["Employee", "Employee Name", "Basic", "Corporate", "Contract", "Communication", "Fuel", "Underground", "Shift", "PSA", "PDA", "Deputation", "Officiating", "Scarcity", "Difficulty", "High Altitude", "Cash Handling", "Component 1", "Amount 1", "Scheme 1", "Bank 1", "Number 1",  "Component 2", "Amount 2", "Scheme 2", "Bank 2", "Number 2", "Component 3", "Amount 3", "Scheme 3", "Bank 3", "Number 3"])
	w.writerow(["Employee", "Employee Name", "Basic", "Corporate", "Contract", "Communication", "Fuel", "Shift", "PSA", "PDA", "Deputation", "Officiating", "Scarcity", "Difficulty", "High Altitude", "Cash Handling", "Component 1", "Amount 1", "Scheme 1", "Bank 1", "Number 1",  "Component 2", "Amount 2", "Scheme 2", "Bank 2", "Number 2", "Component 3", "Amount 3", "Scheme 3", "Bank 3", "Number 3", "Component 4", "Amount 4", "Scheme 4", "Bank 4", "Number 4", "Component 5", "Amount 5", "Scheme 5", "Bank 5", "Number 5", "Component 6", "Amount 6", "Scheme 6", "Bank 6", "Number 6", "Component 7", "Amount 7", "Scheme 7", "Bank 7", "Number 7", "Component 8", "Amount 8", "Scheme 8", "Bank 8", "Number 8", "Component 9", "Amount 9", "Scheme 9", "Bank 9", "Number 9", "Component 10", "Amount 10", "Scheme 10", "Bank 10", "Number 10"])

	# Ver 3.0 Begins, Added by SHIV on 2018/10/24
	# Header
	'''
	cli = frappe.db.sql("""
				select distinct parentfield,salary_component
				from `tabSalary Detail`
				order by parentfield, salary_component
		""")

		frappe.msgprint(_("{0}").format(cli))

	# Transactions
	emp = frappe.db.sql("""
				select name
				from `tabEmployee`
				order by branch
		""", as_dict = True)
	for e in emp:
				rec = []
				earnings = frappe.db.sql_list("""
						select
								(case when salary_component== 'Basic Pay' then amount else 0 end) as basic,
								(case when salary_component== 'Basic Pay' then amount else 0 end) as basic,
						
				""")
	'''
	# Ver 3.0 Ends
	return w

@frappe.whitelist()
def upload():
	if not frappe.has_permission("Salary Structure", "create"):
		raise frappe.PermissionError

	from frappe.utils.csvutils import read_csv_content
	rows = read_csv_content(frappe.local.uploaded_file)
	if not rows:
		frappe.throw(_("Please select a csv file"))
	#frappe.enqueue(import_salary_structures, rows=rows, now=True if len(rows) < 200 else False)
	import_salary_structures(rows)

def import_salary_structures(rows):
	from frappe.modules import scrub

	rows = list(filter(lambda x: x and any(x), rows))
	columns = [scrub(f) for f in rows[2]]
	rows = rows[3:]

	ret = []
	error = False

	from frappe.utils.csvutils import check_record, import_doc

	for i, row in enumerate(rows):
		if not row: continue
		row_idx = i + 3
		d = frappe._dict(zip(columns, row))
		try:
			ear = ded = 0
			sws_amount = flt(frappe.db.get_value("Salary Component", "SWS", "default_amount"))
			ret.append("Row#{0}: {1}, {2}".format(i+1,d.employee,d.employee_name))
			if d.employee:
				emp = frappe.get_doc("Employee", d.employee)

				frappe.publish_realtime('import_ss', dict(
					progress=i,
					total=len(rows)
				))

				if frappe.db.exists("Salary Structure", {"employee": d.employee}):
						ret.append("Salary Structure already created for " + str(d.employee))
						continue

				doc = frappe.new_doc("Salary Structure")
				doc.employee = d.employee
				doc.is_active = 'Yes'
				#doc.from_date = nowdate()
				doc.from_date = emp.date_of_joining
				if d.basic:
					doc.append("earnings",{"salary_component": "Basic Pay", "amount": flt(d.basic)})
					ear += flt(d.basic)	
				else:
					frappe.throw("No Basic Pay record on row " + str(row_idx))
								
				if d.corporate:
					doc.eligible_for_corporate_allowance = 1
					doc.ca = d.corporate
					doc.ca_method = 'Percent'

				if d.contract:
					doc.eligible_for_contract_allowance = 1
					doc.contract_allowance = d.contract
					doc.contract_allowance_method = 'Percent'

				if d.communication:
					doc.eligible_for_communication_allowance = 1
					doc.communication_allowance = d.communication
					doc.communication_allowance_method = 'Lumpsum'

				if d.fuel:
					doc.eligible_for_fuel_allowances = 1
					doc.fuel_allowances = d.fuel
					doc.fuel_allowances_method = 'Lumpsum'

				if d.shift:
					doc.eligible_for_shift = 1
					doc.shift = d.shift
					doc.shift_method = 'Percent'

				if d.psa:
					doc.eligible_for_psa = 1
					doc.psa = d.psa
					doc.psa_method = 'Lumpsum'

				if d.pda:
					doc.eligible_for_pda = 1
					doc.pda = d.pda
					doc.pda_method = 'Percent'

				if d.deputation:
					doc.eligible_for_deputation = 1
					doc.deputation = d.deputation
					doc.deputation_method = 'Percent'

				if d.officiating:
					doc.eligible_for_officiating_allowance = 1
					doc.officiating = d.officiating
					doc.officiating_method = 'Percent'

				if d.scarcity:
					doc.eligible_for_scarcity = 1
					doc.scarcity = d.scarcity
					doc.scarcity_method = 'Percent'

				if d.difficulty:
					doc.eligible_for_difficulty = 1
					doc.difficulty = d.difficulty
					doc.difficulty_method = 'Lumpsum'

				if d.high_altitude:
					doc.eligible_for_high_altitude = 1
					doc.high_altitude = d.high_altitude
					doc.high_altitude_method = 'Lumbsum'

				if d.cash_handling:
					doc.eligible_for_cash_handling = 1
					doc.cash_handling = d.cash_handling
					doc.cash_handling_method = 'Lumpsum'

				if d.amount_1:
					#if d.bank_1 and d.scheme_1 and d.component_1 and d.number_1:
					if d.component_1:
							doc.append("deductions",{"salary_component": str(d.component_1), "amount": flt(d.amount_1), "institution_name": str(d.bank_1) if d.bank_1 else None, "reference_type": str(d.scheme_1) if d.scheme_1 else None, "reference_number": str(d.number_1) if d.number_1 else None})
							ded += flt(d.amount_1)

				if d.amount_2:
					#if d.bank_2 and d.scheme_2 and d.component_2 and d.number_2:
					if d.component_2:
							doc.append("deductions",{"salary_component": str(d.component_2), "amount": flt(d.amount_2), "institution_name": str(d.bank_2) if d.bank_2 else None, "reference_type": str(d.scheme_2) if d.scheme_2 else None, "reference_number": str(d.number_2) if d.number_2 else None})
							ded += flt(d.amount_2)

				if d.amount_3:
					#if d.bank_3 and d.scheme_3 and d.component_3 and d.number_3:
					if d.component_3:
							doc.append("deductions",{"salary_component": str(d.component_3), "amount": flt(d.amount_3), "institution_name": str(d.bank_3) if d.bank_3 else None, "reference_type": str(d.scheme_3) if d.scheme_3 else None, "reference_number": str(d.number_3) if d.number_3 else None})
							ded += flt(d.amount_3)

				if d.amount_4:
					#if d.bank_4 and d.scheme_4 and d.component_4 and d.number_4:
					if d.component_4:
							doc.append("deductions",{"salary_component": str(d.component_4), "amount": flt(d.amount_4), "institution_name": str(d.bank_4) if d.bank_4 else None, "reference_type": str(d.scheme_4) if d.scheme_4 else None, "reference_number": str(d.number_4) if d.number_4 else None})
							ded += flt(d.amount_4)

				if d.amount_5:
					#if d.bank_5 and d.scheme_5 and d.component_5 and d.number_5:
					if d.component_5:
						doc.append("deductions",{"salary_component": str(d.component_5), "amount": flt(d.amount_5), "institution_name": str(d.bank_5) if d.bank_5 else None, "reference_type": str(d.scheme_5) if d.scheme_5 else None, "reference_number": str(d.number_5) if d.number_5 else None})
						ded += flt(d.amount_5)

				if d.amount_6:
					#if d.bank_6 and d.scheme_6 and d.component_6 and d.number_6:
					if d.component_6:
						doc.append("deductions",{"salary_component": str(d.component_6), "amount": flt(d.amount_6), "institution_name": str(d.bank_6) if d.bank_6 else None, "reference_type": str(d.scheme_6) if d.scheme_6 else None, "reference_number": str(d.number_6) if d.number_6 else None})
						ded += flt(d.amount_6)

				if d.amount_7:
					#if d.bank_7 and d.scheme_7 and d.component_7 and d.number_7:
					if d.component_7:
						doc.append("deductions",{"salary_component": str(d.component_7), "amount": flt(d.amount_7), "institution_name": str(d.bank_7) if d.bank_7 else None, "reference_type": str(d.scheme_7) if d.scheme_7 else None, "reference_number": str(d.number_7) if d.number_7 else None})
						ded += flt(d.amount_7)

				if d.amount_8:
					#if d.bank_8 and d.scheme_8 and d.component_8 and d.number_8:
					if d.component_8:
						doc.append("deductions",{"salary_component": str(d.component_8), "amount": flt(d.amount_8), "institution_name": str(d.bank_8) if d.bank_8 else None, "reference_type": str(d.scheme_8) if d.scheme_8 else None, "reference_number": str(d.number_8) if d.number_8 else None})
						ded += flt(d.amount_8)

				if d.amount_9:
					#if d.bank_9 and d.scheme_9 and d.component_9 and d.number_9:
					if d.component_9:
						doc.append("deductions",{"salary_component": str(d.component_9), "amount": flt(d.amount_9), "institution_name": str(d.bank_9) if d.bank_9 else None, "reference_type": str(d.scheme_9) if d.scheme_9 else None, "reference_number": str(d.number_9) if d.number_9 else None})
						ded += flt(d.amount_9)

				if d.amount_10:
					#if d.bank_10 and d.scheme_10 and d.component_10 and d.number_10:
					if d.component_10:
						doc.append("deductions",{"salary_component": str(d.component_10), "amount": flt(d.amount_10), "institution_name": str(d.bank_10) if d.bank_10 else None, "reference_type": str(d.scheme_10) if d.scheme_10 else None, "reference_number": str(d.number_10) if d.number_10 else None})
						ded += flt(d.amount_10)
						
				doc.append("deductions",{"salary_component": "SWS", "amount": sws_amount})	
				ded += sws_amount
				
				if not emp.grade:
					frappe.throw("No Grade assigned to " + str(emp.employee_name))

				doc.insert()
				#doc.submit()
			else:
				frappe.throw("No employee record on row " + str(row_idx))
			
			ret.append("Salary Structure created for " + str(d.employee))
		except AttributeError:
			pass
		except Exception as e:
			#frappe.db.rollback()
			error = True
			ret.append('Error for row (#%d) ' % (row_idx))
			ret.append(str(frappe.get_traceback()))
			frappe.errprint(frappe.get_traceback())
		
	#return {"messages": ret, "error": error}
	if error:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	frappe.publish_realtime('import_ss', dict(
		messages=ret,
		error=error
	))


@frappe.whitelist()
def upload_old():
	if not frappe.has_permission("Salary Structure", "create"):
		raise frappe.PermissionError

	from frappe.utils.csvutils import read_csv_content_from_uploaded_file
	from frappe.modules import scrub
	

	rows = read_csv_content_from_uploaded_file()
	rows = filter(lambda x: x and any(x), rows)
	if not rows:
		msg = [_("Please select a csv file")]
		return {"messages": msg, "error": msg}

	#Columns located at 4th row
	columns = [scrub(f) for f in rows[2]]
	ret = []
	error = False

	from frappe.utils.csvutils import check_record, import_doc

	for i, row in enumerate(rows[3:]):
		if not row: continue
		row_idx = i + 3
		d = frappe._dict(zip(columns, row))
		try:
			ear = ded = 0
			sws_amount = flt(frappe.db.get_value("Salary Component", "SWS", "default_amount"))
			ret.append("Row#{0}: {1}, {2}".format(i+1,d.employee,d.employee_name))
			if d.employee:
				emp = frappe.get_doc("Employee", d.employee)
				
				if frappe.db.exists("Salary Structure", {"employee": d.employee}):
						ret.append("Salary Structure already created for " + str(d.employee))
						continue

				'''
				if frappe.db.exists("Salary Structure", {"employee": d.employee}):
						frappe.delete_doc("Salary Structure", frappe.db.sql_list("""
								select name
								from `tabSalary Structure`
								where employee = '{0}'""".format(d.employee)), for_reload=True)
				'''
				doc = frappe.new_doc("Salary Structure")
				doc.employee = d.employee
				doc.is_active = 'Yes'
				#doc.from_date = nowdate()
				doc.from_date = emp.date_of_joining
				if d.basic:
					doc.append("earnings",{"salary_component": "Basic Pay", "amount": flt(d.basic)})
					ear += flt(d.basic)	
				else:
					frappe.throw("No Basic Pay record on row " + str(row_idx))
								
				if d.corporate:
					doc.eligible_for_corporate_allowance = 1
					doc.ca = d.corporate
					doc.ca_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.corporate)
					#doc.append("earnings",{"salary_component": "Corporate Allowance", "amount": amount})	
					#ear += flt(amount)	
				if d.contract:
					doc.eligible_for_contract_allowance = 1
					doc.contract_allowance = d.contract
					doc.contract_allowance_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.contract)
					#doc.append("earnings",{"salary_component": "Contract Allowance", "amount": amount})	
					#ear += flt(amount)	
				if d.communication:
					doc.eligible_for_communication_allowance = 1
					doc.communication_allowance = d.communication
					doc.communication_allowance_method = 'Lumpsum'
					#amount = flt(d.communication)
					#doc.append("earnings",{"salary_component": "Communication Allowance", "amount": amount})
					#ear += amount	
				if d.fuel:
					doc.eligible_fuel_allowances = 1
					doc.fuel_allowances = d.fuel
					doc.fuel_allowances_method = 'Lumpsum'
					#amount = flt(d.fuel)
					#doc.append("earnings",{"salary_component": "Fuel Allowance", "amount": amount})
					#ear += amount
				'''
				if d.underground:
					doc.eligible_for_underground = 1
					doc.underground = d.underground
					doc.underground_method = 'Percent'
					amount = flt(d.basic) * 0.01 * flt(d.underground)
					doc.append("earnings",{"salary_component": "Underground Allowance", "amount": amount})	
					ear += amount
				'''
				if d.shift:
					doc.eligible_for_shift = 1
					doc.shift = d.shift
					doc.shift_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.shift)
					#doc.append("earnings",{"salary_component": "Shift Allowance", "amount": amount})	
					#ear += amount	
				if d.psa:
					doc.eligible_for_psa = 1
					doc.psa = d.psa
					doc.psa_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.psa)
					#doc.append("earnings",{"salary_component": "PSA", "amount": amount})	
					#ear += amount	
				if d.pda:
					doc.eligible_for_pda = 1
					doc.pda = d.pda
					doc.pda_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.pda)
					#doc.append("earnings",{"salary_component": "PDA", "amount": amount})	
					#ear += amount	
				if d.deputation:
					doc.eligible_for_deputation = 1
					doc.deputation = d.deputation
					doc.deputation_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.deputation)
					#doc.append("earnings",{"salary_component": "Deputation Allowance", "amount": amount})	
					#ear += amount	
				if d.officiating:
					doc.eligible_for_officiating_allowance = 1
					doc.officiating = d.officiating
					doc.officiating_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.officiating)
					#doc.append("earnings",{"salary_component": "Officiating Allowance", "amount": amount})	
					#ear += amount	
				if d.scarcity:
					doc.eligible_for_scarcity = 1
					doc.scarcity = d.scarcity
					doc.scarcity_method = 'Percent'
					#amount = flt(d.basic) * 0.01 * flt(d.scarcity)
					#doc.append("earnings",{"salary_component": "Scarcity Allowance", "amount": amount})	
					#ear += amount	
				if d.difficulty:
					doc.eligible_for_difficulty = 1
					doc.difficulty = d.difficulty
					doc.difficulty_method = 'Lumpsum'
					#amount = flt(d.difficulty)
					#doc.append("earnings",{"salary_component": "Dificult Area Allowance", "amount": amount})
					#ear += amount	
				if d.high_altitude:
					doc.eligible_for_high_altitude = 1
					doc.high_altitude = d.high_altitude
					doc.high_altitude_method = 'Lumbsum'
					#amount = flt(d.high_altitude)
					#doc.append("earnings",{"salary_component": "High Altitude Allowance", "amount": amount})
					#ear += amount	
				if d.cash_handling:
					doc.eligible_for_cash_handling = 1
					doc.cash_handling = d.cash_handling
					doc.cash_handling_method = 'Lumpsum'
					#amount = flt(d.cash_handling)
					#doc.append("earnings",{"salary_component": "Cash Handling Allowance", "amount": amount})
					#ear += amount	

				if d.amount_1:
					#if d.bank_1 and d.scheme_1 and d.component_1 and d.number_1:
					if d.component_1:
							doc.append("deductions",{"salary_component": str(d.component_1), "amount": flt(d.amount_1), "institution_name": str(d.bank_1) if d.bank_1 else None, "reference_type": str(d.scheme_1) if d.scheme_1 else None, "reference_number": str(d.number_1) if d.number_1 else None})
							ded += flt(d.amount_1)

				if d.amount_2:
					#if d.bank_2 and d.scheme_2 and d.component_2 and d.number_2:
					if d.component_2:
							doc.append("deductions",{"salary_component": str(d.component_2), "amount": flt(d.amount_2), "institution_name": str(d.bank_2) if d.bank_2 else None, "reference_type": str(d.scheme_2) if d.scheme_2 else None, "reference_number": str(d.number_2) if d.number_2 else None})
							ded += flt(d.amount_2)

				if d.amount_3:
					#if d.bank_3 and d.scheme_3 and d.component_3 and d.number_3:
					if d.component_3:
							doc.append("deductions",{"salary_component": str(d.component_3), "amount": flt(d.amount_3), "institution_name": str(d.bank_3) if d.bank_3 else None, "reference_type": str(d.scheme_3) if d.scheme_3 else None, "reference_number": str(d.number_3) if d.number_3 else None})
							ded += flt(d.amount_3)

				if d.amount_4:
					#if d.bank_4 and d.scheme_4 and d.component_4 and d.number_4:
					if d.component_4:
							doc.append("deductions",{"salary_component": str(d.component_4), "amount": flt(d.amount_4), "institution_name": str(d.bank_4) if d.bank_4 else None, "reference_type": str(d.scheme_4) if d.scheme_4 else None, "reference_number": str(d.number_4) if d.number_4 else None})
							ded += flt(d.amount_4)

				if d.amount_5:
					#if d.bank_5 and d.scheme_5 and d.component_5 and d.number_5:
					if d.component_5:
						doc.append("deductions",{"salary_component": str(d.component_5), "amount": flt(d.amount_5), "institution_name": str(d.bank_5) if d.bank_5 else None, "reference_type": str(d.scheme_5) if d.scheme_5 else None, "reference_number": str(d.number_5) if d.number_5 else None})
						ded += flt(d.amount_5)

				if d.amount_6:
					#if d.bank_6 and d.scheme_6 and d.component_6 and d.number_6:
					if d.component_6:
						doc.append("deductions",{"salary_component": str(d.component_6), "amount": flt(d.amount_6), "institution_name": str(d.bank_6) if d.bank_6 else None, "reference_type": str(d.scheme_6) if d.scheme_6 else None, "reference_number": str(d.number_6) if d.number_6 else None})
						ded += flt(d.amount_6)

				if d.amount_7:
					#if d.bank_7 and d.scheme_7 and d.component_7 and d.number_7:
					if d.component_7:
						doc.append("deductions",{"salary_component": str(d.component_7), "amount": flt(d.amount_7), "institution_name": str(d.bank_7) if d.bank_7 else None, "reference_type": str(d.scheme_7) if d.scheme_7 else None, "reference_number": str(d.number_7) if d.number_7 else None})
						ded += flt(d.amount_7)

				if d.amount_8:
					#if d.bank_8 and d.scheme_8 and d.component_8 and d.number_8:
					if d.component_8:
						doc.append("deductions",{"salary_component": str(d.component_8), "amount": flt(d.amount_8), "institution_name": str(d.bank_8) if d.bank_8 else None, "reference_type": str(d.scheme_8) if d.scheme_8 else None, "reference_number": str(d.number_8) if d.number_8 else None})
						ded += flt(d.amount_8)

				if d.amount_9:
					#if d.bank_9 and d.scheme_9 and d.component_9 and d.number_9:
					if d.component_9:
						doc.append("deductions",{"salary_component": str(d.component_9), "amount": flt(d.amount_9), "institution_name": str(d.bank_9) if d.bank_9 else None, "reference_type": str(d.scheme_9) if d.scheme_9 else None, "reference_number": str(d.number_9) if d.number_9 else None})
						ded += flt(d.amount_9)

				if d.amount_10:
					#if d.bank_10 and d.scheme_10 and d.component_10 and d.number_10:
					if d.component_10:
						doc.append("deductions",{"salary_component": str(d.component_10), "amount": flt(d.amount_10), "institution_name": str(d.bank_10) if d.bank_10 else None, "reference_type": str(d.scheme_10) if d.scheme_10 else None, "reference_number": str(d.number_10) if d.number_10 else None})
						ded += flt(d.amount_10)
						
				doc.append("deductions",{"salary_component": "SWS", "amount": sws_amount})	
				ded += sws_amount
				
				if not emp.employee_subgroup:
					frappe.throw("No Grade assigned to " + str(emp.employee_name))

				'''
				gis_amount = flt(frappe.db.get_value("Employee Grade", emp.employee_subgroup, "gis"))
				doc.append("deductions",{"salary_component": "Group Insurance Scheme", "amount": gis_amount})	
				ded += gis_amount

				ded_percent = get_company_pf()
				pf_amount = flt(d.basic) * 0.01 * flt(ded_percent[0][0])
				doc.append("deductions",{"salary_component": "PF", "amount": pf_amount})	
				ded += pf_amount
				
				health_amount = flt(ear) * 0.01 * flt(ded_percent[0][2])
				doc.append("deductions",{"salary_component": "Health Contribution", "amount": health_amount})	
				ded += health_amount
				
				tax_gross = flt(ear) - flt(pf_amount) - flt(gis_amount)
				if d.communication:
					tax_gross -= (0.5 * flt(d.communication))
				tax_amount = get_salary_tax(tax_gross)
				doc.append("deductions",{"salary_component": "Salary Tax", "amount": tax_amount})	
				ded += tax_amount
				
				doc.total_earning = flt(ear)
				doc.total_deduction = flt(ded)
				doc.net_pay = flt(ear) - flt(ded)
				'''
				doc.insert()
			else:
				frappe.throw("No employee record on row " + str(row_idx))
			
			ret.append("Salary Structure created for " + str(d.employee))
		except Exception as e:
			frappe.db.rollback()
			error = True
			ret.append('Error for row (#%d) ' % (row_idx))
			ret.append(str(frappe.get_traceback()))
			frappe.errprint(frappe.get_traceback())
		
	return {"messages": ret, "error": error}

	'''
	for i, row in enumerate(rows[3:]):
		if not row: continue
		row_idx = i + 3
		d = frappe._dict(zip(columns, row))
		try:
			ear = ded = 0
			sws_amount = flt(frappe.db.get_value("Salary Component", "SWS", "default_amount"))
			doc = frappe.new_doc("Salary Structure")
			if d.employee:
				emp = frappe.get_doc("Employee", d.employee)
				doc.employee = d.employee
				doc.is_active = 'Yes'
				doc.from_date = nowdate()
				if d.basic:
					doc.append("earnings",{"salary_component": "Basic Pay", "amount": flt(d.basic)})
					ear += flt(d.basic)	
				else:
					frappe.throw("No Basic Pay record on row " + str(row_idx))
				if d.corporate:
					doc.eligible_for_corporate_allowance = 1
					doc.ca = d.corporate
					amount = flt(d.basic) * 0.01 * flt(d.corporate)
					doc.append("earnings",{"salary_component": "Corporate Allowance", "amount": amount})	
					ear += flt(amount)	
				if d.contract:
					doc.eligible_for_contract_allowance = 1
					doc.contract_allowance = d.contract
					amount = flt(d.basic) * 0.01 * flt(d.contract)
					doc.append("earnings",{"salary_component": "Contract Allowance", "amount": amount})	
					ear += flt(amount)	
				if d.communication:
					doc.eligible_for_communication_allowance = 1
					doc.communication_allowance = d.communication
					amount = flt(d.communication)
					doc.append("earnings",{"salary_component": "Communication Allowance", "amount": amount})
					ear += amount	
				if d.fuel:
					doc.eligible_fuel_allowances = 1
					doc.fuel_allowances = d.fuel
					amount = flt(d.fuel)
					doc.append("earnings",{"salary_component": "Fuel Allowance", "amount": amount})
					ear += amount	
				if d.underground:
					doc.eligible_for_underground = 1
					doc.underground = d.underground
					amount = flt(d.basic) * 0.01 * flt(d.underground)
					doc.append("earnings",{"salary_component": "Underground Allowance", "amount": amount})	
					ear += amount	
				if d.shift:
					doc.eligible_for_shift = 1
					doc.shift = d.shift
					amount = flt(d.basic) * 0.01 * flt(d.shift)
					doc.append("earnings",{"salary_component": "Shift Allowance", "amount": amount})	
					ear += amount	
				if d.psa:
					doc.eligible_for_psa = 1
					doc.psa = d.psa
					amount = flt(d.basic) * 0.01 * flt(d.psa)
					doc.append("earnings",{"salary_component": "PSA", "amount": amount})	
					ear += amount	
				if d.pda:
					doc.eligible_for_pda = 1
					doc.psa = d.pda
					amount = flt(d.basic) * 0.01 * flt(d.pda)
					doc.append("earnings",{"salary_component": "PDA", "amount": amount})	
					ear += amount	
				if d.deputation:
					doc.eligible_for_deputation = 1
					doc.deputation = d.deputation
					amount = flt(d.basic) * 0.01 * flt(d.deputation)
					doc.append("earnings",{"salary_component": "Deputation Allowance", "amount": amount})	
					ear += amount	
				if d.officiating:
					doc.eligible_for_officiating_allowance = 1
					doc.officiating = d.officiating
					amount = flt(d.basic) * 0.01 * flt(d.officiating)
					doc.append("earnings",{"salary_component": "Officiating Allowance", "amount": amount})	
					ear += amount	
				if d.scarcity:
					doc.eligible_for_scarcity = 1
					doc.scarcity = d.scarcity
					amount = flt(d.basic) * 0.01 * flt(d.scarcity)
					doc.append("earnings",{"salary_component": "Scarcity Allowance", "amount": amount})	
					ear += amount	
				if d.difficulty:
					doc.eligible_for_difficulty = 1
					doc.difficulty = d.difficulty
					amount = flt(d.difficulty)
					doc.append("earnings",{"salary_component": "Dificult Area Allowance", "amount": amount})
					ear += amount	
				if d.high_altitude:
					doc.eligible_for_high_altitude = 1
					doc.high_altitude = d.high_altitude
					amount = flt(d.high_altitude)
					doc.append("earnings",{"salary_component": "High Altitude Allowance", "amount": amount})
					ear += amount	
				if d.cash_handling:
					doc.eligible_for_cash_handling = 1
					doc.cash_handling = d.cash_handling
					amount = flt(d.cash_handling)
					doc.append("earnings",{"salary_component": "Cash Handling Allowance", "amount": amount})
					ear += amount	

				if d.amount_1:
					if d.bank_1 and d.scheme_1 and d.component_1 and d.number_1:
						doc.append("deductions",{"salary_component": str(d.component_1), "amount": flt(d.amount_1), "institution_name": str(d.bank_1), "reference_type": str(d.scheme_1), "reference_number": str(d.number_1)})	
						ded += flt(d.amount_1)

				if d.amount_2:
					if d.bank_2 and d.scheme_2 and d.component_2 and d.number_2:
						doc.append("deductions",{"salary_component": str(d.component_2), "amount": flt(d.amount_2), "institution_name": str(d.bank_2), "reference_type": str(d.scheme_2), "reference_number": str(d.number_2)})	
						ded += flt(d.amount_2)

				if d.amount_3:
					if d.bank_3 and d.scheme_3 and d.component_3 and d.number_3:
						doc.append("deductions",{"salary_component": str(d.component_3), "amount": flt(d.amount_3), "institution_name": str(d.bank_3), "reference_type": str(d.scheme_3), "reference_number": str(d.number_3)})	
						ded += flt(d.amount_3)

				doc.append("deductions",{"salary_component": "SWS", "amount": sws_amount})	
				ded += sws_amount
				
				if not emp.employee_subgroup:
					frappe.throw("No Grade assigned to " + str(emp.employee_name))
				
				gis_amount = flt(frappe.db.get_value("Employee Grade", emp.employee_subgroup, "gis"))
				doc.append("deductions",{"salary_component": "Group Insurance Scheme", "amount": gis_amount})	
				ded += gis_amount

				ded_percent = get_company_pf()
				pf_amount = flt(d.basic) * 0.01 * flt(ded_percent[0][0])
				doc.append("deductions",{"salary_component": "PF", "amount": pf_amount})	
				ded += pf_amount
				
				health_amount = flt(ear) * 0.01 * flt(ded_percent[0][2])
				doc.append("deductions",{"salary_component": "Health Contribution", "amount": health_amount})	
				ded += health_amount
				
				tax_gross = flt(ear) - flt(pf_amount) - flt(gis_amount)
				if d.communication:
					tax_gross -= (0.5 * flt(d.communication))
				tax_amount = get_salary_tax(tax_gross)
				doc.append("deductions",{"salary_component": "Salary Tax", "amount": tax_amount})	
				ded += tax_amount
				
				doc.total_earning = flt(ear)
				doc.total_deduction = flt(ded)
				doc.net_pay = flt(ear) - flt(ded)
				doc.insert()
			else:
				frappe.throw("No employee record on row " + str(row_idx))
			
			ret.append("Salary Structure created for " + str(d.employee))
		except Exception, e:
			frappe.db.rollback()
			error = True
			ret.append('Error for row (#%d) ' % (row_idx))
			ret.append(str(frappe.get_traceback()))
			frappe.errprint(frappe.get_traceback())
		
	return {"messages": ret, "error": error}
	'''
 
