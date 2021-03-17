# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, money_in_words, getdate, date_diff, today, add_days, get_first_day, get_last_day
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
import collections
from erpnext.hr.doctype.travel_authorization.travel_authorization import get_exchange_rate
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class TravelClaim(Document):
	def validate(self):
		hr_role = frappe.db.get_value("UserRole", {"parent": frappe.session.user, "role": "HR User"}, "role")
		#if frappe.session.user == self.supervisor and not self.supervisor_approval:
		#	self.db_set("supervisor_approved_on", '')
		#	self.supervisor_approved_on = ''
		#if self.supervisor_approved_on and not hr_role:
		#	frappe.throw("Cannot change records after approval by supervisor")
		validate_workflow_states(self)
		#self.check_return_date()
		self.validate_dates()
		self.check_approval()
		self.validate_dsa_ceiling()
		employee = frappe.db.get_value("Employee", self.employee, "user_id")
		# Following line commented by SHIV on 2020/09/22 as the same code is taken care in on_submit
		#self.update_travel_authorization()
		self.update_amounts()
		
		# Following code commented by SHIV on 2020/10/04
		'''
		if frappe.session.user == self.owner or frappe.session.user == employee:
			self.db_set("claim_status", "")
			self.sendmail(frappe.db.get_value("Employee", {"user_id": self.supervisor}, "name"), "Travel Claim Submitted", str(self.employee_name) + " has requested you to verify and sign a " + str(frappe.get_desk_link("Travel Claim", self.name)))
		elif self.claim_status == "Rejected by Supervisor":
			self.sendmail(self.employee, "Travel Claim Rejected by Supervisor" + str(self.name), "Following remarks has been added by the supervisor: \n" + str(self.reason))
		elif self.claim_status == "Rejected by HR":
			self.sendmail(self.employee, "Travel Claim Rejected by HR" + str(self.name), "Following remarks has been added from HR: \n" + str(self.reason))

		if frappe.session.user == self.supervisor and self.supervisor_approval:
			self.db_set("supervisor_approved_on", nowdate())
		'''
		notify_workflow_states(self)

	def on_update(self):
		self.check_double_dates()

	def on_submit(self):
		#self.get_status()
		#self.validate_submitter()
		#self.check_status()
		self.post_journal_entry()
		self.update_travel_authorization()

		if self.supervisor_approval and self.hr_approval:
			self.db_set("hr_approved_on", nowdate())
		
		# Following line commented by SHIV on 2020/10/04
		#self.sendmail(self.employee, "Travel Claim Approved" + str(self.name), "Your " + str(frappe.get_desk_link("Travel Claim", self.name)) + " has been approved and sent to Accounts Section. Kindly follow up.")
		notify_workflow_states(self)

	def before_cancel(self):
		self.unlink_travel_authorization()

	def on_cancel_after_draft(self):
		validate_workflow_states(self)
		notify_workflow_states(self)

	def on_cancel(self):
		self.check_journal_entry()
		# Following line commented by SHIV on 2020/10/04
		#self.sendmail(self.employee, "Travel Claim Cancelled by HR" + str(self.name), "Your travel claim " + str(self.name) + " has been cancelled by the user")
		notify_workflow_states(self)

	# Following method created by SHIV on 2020/09/22
	def check_journal_entry(self):
		if self.claim_journal and frappe.db.exists("Journal Entry", {"name": self.claim_journal, "docstatus": ("<","2")}):
			frappe.throw(_("You need to cancel {} first").format(frappe.get_desk_link("Journal Entry", self.claim_journal)))

	# Following method added by SHIV on 2020/09/22
	def before_cancel_after_draft(self):
		self.unlink_travel_authorization()

	def unlink_travel_authorization(self):
		cl_status = frappe.db.get_value("Journal Entry", self.claim_journal, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the claim journal entry first!")

		tas = frappe.db.sql("select distinct(travel_authorization) as ta from `tabTravel Claim Item` where parent = %s", str(self.name), as_dict=True)
		for a in tas:
			ta = frappe.get_doc("Travel Authorization", a.ta)
			ta.db_set("travel_claim", "")

		if self.ta:
			travel_a = frappe.get_doc("Travel Authorization", self.ta)
			travel_a.db_set("travel_claim","")

	def get_monthly_count(self, items):
			counts = {}
			for i in items:
					i.till_date     = i.date if not i.till_date else i.till_date
					from_month      = str(i.date)[5:7]
					to_month        = str(i.till_date)[5:7]
					from_year       = str(i.date)[:4]
					to_year         = str(i.till_date)[:4]
					from_monthyear  = str(from_year)+str(from_month)
					to_monthyear    = str(to_year)+str(to_month)

					if int(to_monthyear) >= int(from_monthyear):
							for y in range(int(from_year), int(to_year)+1):
									m_start = from_month if str(y) == str(from_year) else '01'
									m_end   = to_month if str(y) == str(to_year) else '12'
													
									for m in range(int(m_start), int(m_end)+1):
											key          = str(y)+str(m).rjust(2,str('0'))
											m_start_date = key[:4]+'-'+key[4:]+'-01'
											m_start_date = i.date if str(y)+str(m).rjust(2,str('0')) == str(from_year)+str(from_month) else m_start_date
											m_end_date   = i.till_date if str(y)+str(m).rjust(2,str('0')) == str(to_year)+str(to_month) else get_last_day(m_start_date)
											if counts.has_key(key):
													counts[key] += date_diff(m_end_date, m_start_date)+1
											else:
													counts[key] = date_diff(m_end_date, m_start_date)+1
					else:
							frappe.throw(_("Row#{0} : Till Date cannot be before from date.").format(i.idx), title="Invalid Data")
			return collections.OrderedDict(sorted(counts.items()))
	
	def validate_dsa_ceiling(self):
			max_days_per_month  = 0
			tt_list             = []
			local_count         = {}
			claimed_count       = {}
			mapped_count        = {}
			months              = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
			cond1               = ""
			cond2               = ""
			cond3               = ""
			format_string       = ""
			lastday_dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
			
			if self.place_type.lower().replace("-","") == "incountry":
					max_days_per_month = frappe.db.get_single_value("HR Settings", "max_days_incountry")
					if max_days_per_month:
							tt_list = frappe.db.sql_list("select travel_type from `tabHR Settings Incountry`")
			else:
					max_days_per_month = frappe.db.get_single_value("HR Settings", "max_days_outcountry")
					if max_days_per_month:
							tt_list = frappe.db.sql_list("select travel_type from `tabHR Settings Outcountry`")

			if tt_list:
					format_string = ("'"+"','".join(['%s'] * len(tt_list))+"'") % tuple(tt_list)
					cond1 += "and t1.travel_type in ({0}) ".format(format_string, self.travel_type)

			if max_days_per_month and (not tt_list or self.travel_type in (format_string)):
					local_count    = self.get_monthly_count(self.items)
					for k in local_count:
							cond2 += " '{0}' between date_format(t2.`date`,'%Y%m') and date_format(ifnull(t2.`till_date`,t2.`date`),'%Y%m') or".format(k)
					cond2 = cond2.rsplit(' ',1)[0]
					cond2 = "and (" + cond2 + ")"
					cond3 = "and t2.last_day = 0" if not lastday_dsa_percent else ""

					query = """
									select
											t2.date,
											t2.till_date,
											t2.no_days
									from
											`tabTravel Claim` as t1,
											`tabTravel Claim Item` as t2
									where t1.employee = '{0}'
									and t1.docstatus = 1
									and t1.place_type = '{1}'
									{2}                                        
									and t2.parent = t1.name
									{3}
									{4}
					""".format(self.employee, self.place_type, cond1, cond2, cond3)

					tc_list = frappe.db.sql(query, as_dict=True)

					if tc_list:
							claimed_count = self.get_monthly_count(tc_list)

					for k,v in local_count.iteritems():
							mapped_count[k] = {'local': v, 'claimed': claimed_count.get(k,0), 'balance': flt(max_days_per_month)-flt(claimed_count.get(k,0))}

					for i in self.get("items"):
							i.remarks        = ""
							i.days_allocated = 0                                
							if i.last_day and not lastday_dsa_percent:
									i.days_allocated = 0
									continue
							
							record_count     = self.get_monthly_count([i])
							for k,v in record_count.iteritems():                
									lapsed  = 0
									counter = 0
									if mapped_count[k]['balance'] >= v:
											i.days_allocated = flt(i.days_allocated) + v
											mapped_count[k]['balance'] -= v
									else:
											if mapped_count[k]['balance'] < 0:
													lapsed = v
											else:
													lapsed = v - mapped_count[k]['balance']
													i.days_allocated = flt(i.days_allocated) + mapped_count[k]['balance']
													mapped_count[k]['balance'] = 0
													
											if lapsed:
													counter += 1
													frappe.msgprint(_("Row#{0}: You have crossed the DSA({4} days) limit by {1} days for the month {2}-{3}").format(i.idx, int(lapsed), months[int(str(k)[4:])-1], str(k)[:4],max_days_per_month))
													i.remarks = str(i.remarks)+"{3}) {0} Day(s) lapsed for the month {1}-{2}\n".format(int(lapsed), months[int(str(k)[4:])-1], str(k)[:4], counter)
			else:
					for i in self.get("items"):
							i.remarks        = ""
							i.days_allocated = 0 if i.last_day and not lastday_dsa_percent else i.no_days 

	def update_amounts(self):
			#dsa_per_day         = flt(frappe.db.get_value("Employee Grade", self.grade, "dsa"))
			lastday_dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
			total_claim_amount  = 0
			exchange_rate       = 0
			company_currency    = "BTN"
			
			for i in self.get("items"):
					exchange_rate      = 1 if i.currency == company_currency else get_exchange_rate(i.currency, company_currency)
					#i.dsa             = flt(dsa_per_day)
					i.dsa              = flt(i.dsa)
					##### Ver 3.0.190213 Begins, Following line replaced by SHIV on 13/02/2019
					#i.dsa_percent      = lastday_dsa_percent if i.last_day else i.dsa_percent
					i.dsa_percent      = (i.dsa_percent if cint(i.dsa_percent) <= cint(lastday_dsa_percent) else lastday_dsa_percent) if i.last_day else i.dsa_percent
					##### Ver 3.0.190213 Ends
					i.amount           = (flt(i.days_allocated)*(flt(i.dsa)*flt(i.dsa_percent)/100)) + (flt(i.mileage_rate) * flt(i.distance))
					i.actual_amount    = flt(i.amount) * flt(exchange_rate)
					total_claim_amount = flt(total_claim_amount) +  flt(i.actual_amount)

			self.total_claim_amount = flt(total_claim_amount)
			self.balance_amount     = flt(self.total_claim_amount) + flt(self.extra_claim_amount) - flt(self.advance_amount)

			if flt(self.balance_amount) < 0:
					frappe.throw(_("Balance Amount cannot be a negative value."), title="Invalid Amount")
				
	def check_return_date(self):
				pass
				"""
		dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
				percent = flt(flt(dsa_percent) / 100.0)
		total_claim_amount = 0
		for a in self.items:
			if a.last_day:
				a.dsa_percent = dsa_percent
				a.amount = flt(a.amount) * percent
				a.actual_amount = flt(a.amount) * flt(a.exchange_rate)
			total_claim_amount = total_claim_amount + a.actual_amount
		self.total_claim_amount = total_claim_amount
		self.balance_amount = flt(self.total_claim_amount) + flt(self.extra_claim_amount) - flt(self.advance_amount)
		"""

	def check_double_dates(self):
		if self.items:
			start_date = self.items[0].date
			end_date = self.items[len(self.items) - 1].till_date
			if not end_date:
				end_date = self.items[len(self.items) - 1].date

			tas = frappe.db.sql("select a.name from `tabTravel Claim` a, `tabTravel Claim Item` b where a.employee = %s and a.docstatus = 1 and a.name = b.parent and (b.date between %s and %s or %s between b.date and b.till_date or %s between b.date and b.till_date) and a.name != %s and a.travel_type = %s and a.place_type = %s", (str(self.employee), str(start_date), str(end_date), str(start_date), str(end_date), str(self.name), str(self.travel_type), str(self.place_type)), as_dict=True)
			if tas:
				frappe.throw("The dates in your current Travel Claim has already been claimed in " + str(tas[0].name))

	##
	# make necessary journal entry
	##
	def post_journal_entry(self):
		cost_center = frappe.db.get_value("Employee", self.employee, "cost_center")
		if not cost_center:
			frappe.throw("Setup Cost Center for employee in Employee Information")
		expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		if not expense_bank_account:
			frappe.throw("Setup Default Expense Bank Account for your Branch")
		
		gl_account = ""	
		if self.travel_type == "Travel":
			if self.place_type == "In-Country":
				gl_account =  "travel_incountry_account"
			else:
				gl_account = "travel_outcountry_account"
		elif self.travel_type == "Training":
			if self.place_type == "In-Country":
				gl_account = "training_incountry_account"
			else:
				gl_account = "training_outcountry_account"
		else:
			if self.place_type == "In-Country":
				gl_account = "meeting_and_seminars_in_account"
			else:
				gl_account = "meeting_and_seminars_out_account"
		
		expense_account = frappe.db.get_single_value("HR Accounts Settings", gl_account)
		if not expense_account:
			frappe.throw("Setup Travel/Training Accounts in HR Accounts Settings")

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "Travel Claim (" + self.employee_name + "  " + self.name + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'Claim payment against : ' + self.name;
		je.posting_date = self.posting_date
		je.branch = self.branch

		total_amt = flt(self.total_claim_amount) + flt(self.extra_claim_amount)
	
		je.append("accounts", {
				"account": expense_account,
				"reference_type": "Travel Claim",
				"reference_name": self.name,
				"cost_center": cost_center,
				"debit_in_account_currency": flt(total_amt),
				"debit": flt(total_amt),
				"business_activity": self.business_activity,
			})
		
		advance_amt = flt(self.advance_amount)
		bank_amt = flt(self.balance_amount)

		if (self.advance_amount) > 0:
			advance_account = frappe.db.get_single_value("HR Accounts Settings", "employee_advance_travel")
			if not advance_account:
				frappe.throw("Setup Advance to Employee (Travel) in HR Accounts Settings")
			if flt(self.balance_amount) <= 0:
				advance_amt = total_amt

			je.append("accounts", {
				"account": advance_account,
				"party_type": "Employee",
				"party": self.employee,
				"reference_type": "Travel Claim",
				"reference_name": self.name,
				"cost_center": cost_center,
				"credit_in_account_currency": advance_amt,
				"credit": advance_amt,
				"business_activity": self.business_activity,
			})


		if flt(self.balance_amount) > 0:
			je.append("accounts", {
					"account": expense_bank_account,
					"reference_type": "Travel Claim",
					"reference_name": self.name,
					"cost_center": cost_center,
					"credit_in_account_currency": bank_amt,
					"credit": bank_amt,
					"business_activity": self.business_activity,
				})

		je.insert()
	
		#Set a reference to the claim journal entry
		self.db_set("claim_journal", je.name)
	
	##
	# Update the claim reference on travel authorization
	##
	def update_travel_authorization(self):
		for i in self.get("items"):	
			ta = frappe.get_doc("Travel Authorization", i.travel_authorization)
			if ta.travel_claim and ta.travel_claim != self.name:
				frappe.throw("A travel claim <b>" + str(ta.travel_claim) + "</b> has already been created for the authorization <b>" + str(i.travel_authorization) + "</b>")
			ta.db_set("travel_claim", self.name)

	##
	# Allow only approved authorizations to be submitted
	##
	def check_status(self):
		if self.supervisor_approval == 1 and self.hr_approval == 1:
			pass
		else:
			frappe.throw("Both Supervisor and HR has to approve to submit the travel claim")
	
	##
	# Allow only approved authorizations to be submitted
	##
	def check_approval(self):
		if self.supervisor_approval == 0 and self.hr_approval == 1:
			frappe.throw("Supervisor has to approve the claim before HR")
	
	##
	#Ensure the dates are consistent
	##
	def validate_dates(self):
		if self.ta_date > self.posting_date:
			frappe.throw("The Travel Claim Date cannot be earlier than Travel Authorization Date")

	##
	# Allow only the approver to submit the document
	##
	#def validate_submitter(self):
	#	hr_role = frappe.db.get_value("UserRole", {"parent": frappe.session.user, "role": "HR User"}, "role")
	#	if not hr_role:
	#		frappe.throw("Only a HR User can submit this document")

	##
	# Send notification to the supervisor / employee
	##
	def sendmail(self, to_email, subject, message):
		email = frappe.db.get_value("Employee", to_email, "user_id")
		if email:
			try:
				frappe.sendmail(recipients=email, sender=None, subject=subject, message=message)
			except:
				pass


@frappe.whitelist()
def get_travel_detail(employee, start_date, end_date, place_type, travel_type):
	if employee and start_date and end_date and place_type and travel_type:
		data=[]
		query1 = "select name, dsa_per_day, currency, advance_amount from `tabTravel Authorization`  \
			where posting_date between \'"+ str(start_date) +"\' and \'"+ str(end_date) +"\' \
			and employee = \'"+ str(employee) + "\' and place_type = \'"+ str(place_type) + "\' \
			and travel_type = \'"+ str(travel_type) + "\' and docstatus = 1 and (travel_claim ='' or travel_claim is NULL)"

		for b in frappe.db.sql(query1, as_dict=True):
			for a in frappe.db.sql("select halt, from_place, to_place, date, no_days, till_date, \
				halt_to_date, halt_at, no_days from `tabTravel Authorization Item` i \
				where i.parent = %s order by `date`",b.name, as_dict=True):
				if b.currency == "BTN":
					exchange_rate = 1
				else:
					exchange_rate = frappe.db.get_value("Currency Exchange", {"from_currency": b.currency, "to_currency": "BTN"}, "exchange_rate")
				data.append({"name":b.name, "halt":a.halt, "from_place":a.from_place, "to_place":a.to_place, "date":a.date, "no_days":a.no_days, "till_date":a.till_date, "halt_at":a.halt_at, "dsa_per_day":b.dsa_per_day, "currency":b.currency, "exchange_rate":exchange_rate, "dsa_percent":100, "last_day":0, "advance_amount":0})
					
			data[len(data)-1]['last_day'] = 1
			dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
			data[len(data)-1]['dsa_percent'] = dsa_percent
			data[len(data)-1]['advance_amount'] = b.advance_amount
			
		return data

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabTravel Claim`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabTravel Claim`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabTravel Claim`.supervisor = '{user}' and `tabTravel Claim`.workflow_state != 'Draft')
	)""".format(user=user)

