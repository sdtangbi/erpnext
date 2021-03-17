# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

'''
------------------------------------------------------------------------------------------------------------------------------------------
Version          Author         Ticket#           CreatedOn          ModifiedOn          Remarks
------------ --------------- --------------- ------------------ -------------------  -----------------------------------------------------
3.0               SHIV		                   28/01/2019                          Original Version
------------------------------------------------------------------------------------------------------------------------------------------                                                                          
'''

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, cint, flt
from erpnext.hr.doctype.approver_settings.approver_settings import get_final_approver
from erpnext.hr.hr_custom_functions import get_officiating_employee

class CustomWorkflow:
	def __init__(self, doc):
		self.doc = doc
		self.old_state 		= self.doc.get_db_value("workflow_state")
		self.new_state 		= self.doc.workflow_state
		self.field_map 		= get_field_map()
		self.doc_approver	= self.field_map[self.doc.doctype]
		self.field_list		= ["user_id","employee_name","designation","name"]

		self.employee		= frappe.db.get_value("Employee", self.doc.employee, self.field_list)
		self.reports_to		= frappe.db.get_value("Employee", frappe.db.get_value("Employee", self.doc.employee, "reports_to"), self.field_list)
		self.login_user		= frappe.db.get_value("Employee", {"user_id": frappe.session.user}, self.field_list)
		self.hr_approver	= frappe.db.get_value("Employee", frappe.db.get_single_value("HR Settings", "hr_approver"), self.field_list)
		self.ceo			= frappe.db.get_value("Employee", frappe.db.get_value("Employee", {"grade": "CEO", "status": "Active"}), self.field_list)
		self.dept_approver	= frappe.db.get_value("Employee", frappe.db.get_value("Department", frappe.db.get_value("Employee", self.doc.employee, "department"), "approver"), self.field_list)
		#self.final_approver= frappe.db.get_value("Employee", {"user_id": get_final_approver(doc.branch)}, self.field_list)
		self.final_approver	= []

		if not self.login_user and frappe.session.user != "Administrator":
			frappe.throw("{0} is not added as the employee".format(frappe.session.user))

	def apply_workflow(self):
		if (self.doc.doctype not in self.field_map) or not frappe.db.exists("Workflow", {"document_type": self.doc.doctype, "is_active": 1}):
			return

		if self.doc.doctype == "Leave Application":
			self.leave_application()	
		elif self.doc.doctype == "Leave Encashment":
			self.leave_encashment()
		elif self.doc.doctype == "Salary Advance":
			self.salary_advance()
		elif self.doc.doctype == "Travel Authorization":
			self.travel_authorization()
		elif self.doc.doctype == "Travel Claim":
			self.travel_claim()
		elif self.doc.doctype == "Overtime Application":
			self.overtime_application()
		elif self.doc.doctype == "Material Request":
			self.material_request()
		else:
			frappe.throw(_("Workflow not defined for {}").format(self.doc.doctype))

	def leave_application(self):
		''' Leave Application Workflow
			1. Casual Leave, Earned Leave & Paternity Leave: 
				* Employee -> Supervisor
			2. Medical Leave:
				* Employee -> Department Head (if the leave is within 5 days)
				* Employee -> CEO (more than 5 days)
			3. Bereavement & Maternity:
				* Employee -> Department Head
			4. Extraordinary Leave:
				* Employee -> CEO 
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting Approval".lower()):
			if self.doc.leave_type in ("Casual Leave", "Earned Leave", "Paternity Leave"):
				self.set_approver("Supervisor")
			elif self.doc.leave_type in ("Medical Leave"):
				if flt(self.doc.total_leave_days) <= 5:
					self.set_approver("Department Head")
					# when Department Head himself/herself applies, request should go to their reports_to
					if self.doc.leave_approver == self.employee[0]:
						self.set_approver("Supervisor")
				else:
					self.set_approver("CEO")
					# when CEO himself/herself applies, request should go to their reports_to
					if self.doc.leave_approver == self.employee[0]:
						self.set_approver("Supervisor")
			elif self.doc.leave_type in ("Bereavement Leave", "Maternity Leave"):
				self.set_approver("Department Head")
				# when Department Head himself/herself applies, request should go to their reports_to
				if self.doc.leave_approver == self.employee[0]:
					self.set_approver("Supervisor")
			elif self.doc.leave_type in ("EOL", "Extraordinary Leave"):
				self.set_approver("CEO")
				# when CEO himself/herself applies, request should go to their reports_to
				if self.doc.leave_approver == self.employee[0]:
					self.set_approver("Supervisor")
			else:
				frappe.throw(_("Workflow not defined for leave type {}").format(self.doc.leave_type))
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Leave Application".format(self.doc.leave_approver_name))
			self.doc.status= "Approved"
			self.update_employment_status()		
		elif self.new_state.lower() == "Rejected".lower():
			if self.doc.leave_approver != frappe.session.user:
				frappe.throw("Only {} can Reject this Leave Application".format(self.doc.leave_approver_name))
			self.doc.status = "Rejected"
		elif self.new_state.lower() == "Cancelled".lower():
			if frappe.session.user not in (self.doc.leave_approver,"Administrator"):
				frappe.throw(_("Only {} can Cancel this Leave Application").format(self.doc.leave_approver_name))
		else:
			frappe.throw(_("Invalid Workflow State {}").format(self.doc.workflow_state))

	def leave_encashment(self):
		''' Leave Encashment Workflow
			1. Employee -> Supervisor -> HR
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Waiting HR Approval".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this Leave Encashment".format(self.doc.approver_name))
			self.set_approver("HR")
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve the Travel Claim".format(self.doc.approver_name))
		elif self.new_state.lower() in ('Rejected', 'Rejected By Supervisor'):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Reject the Travel Claim".format(self.doc.approver_name))

	def salary_advance(self):
		''' Salary Advance Workflow
			1. Employee -> CEO -> HR
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting CEO Approval".lower()):
			self.set_approver("CEO")
		elif self.new_state.lower() in ("Waiting HR Approval".lower()):
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw(_("Only {} can Approve this request").format(self.doc.advance_approver_name))
			self.set_approver("HR")
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw(_("Only {} can Approve this request").format(self.doc.advance_approver_name))		
		elif self.new_state.lower() == "Rejected":
			if self.doc.advance_approver != frappe.session.user:
				frappe.throw(_("Only {} can Reject this request").format(self.doc.advance_approver_name))		
		elif self.new_state.lower() == "Cancelled".lower():
			if frappe.session.user not in (self.doc.advance_approver,"Administrator"):
				frappe.throw(_("Only {} can Cancel this document.").format(self.doc.advance_approver_name))

	def travel_authorization(self):
		''' Travel Authorization Workflow
			1. Employee -> Supervisor
		'''
		if self.new_state.lower() in ("Draft".lower(), "Waiting Approval".lower()):
			self.set_approver("Supervisor")
			self.doc.document_status = "Draft"
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.supervisor_name))
			self.doc.document_status = "Approved"
		elif self.new_state.lower() == 'Rejected'.lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Reject this request".format(self.doc.supervisor_name))
			self.doc.document_status = "Rejected"
		elif self.new_state.lower() == "Cancelled".lower():
			if frappe.session.user not in (doc.get(document_approver[0]),"Administrator"):
				frappe.throw(_("Only {} can Cancel this document.").format(self.doc.supervisor_name))
			self.doc.document_status = "Cancelled"

	def travel_claim(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Waiting HR Approval".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.supervisor_name))
			self.set_approver("HR")
			self.doc.supervisor_approval = 1
		elif self.new_state.lower() == "Claimed".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.supervisor))
			self.doc.status = "Claimed"
			self.doc.hr_approval = 1
			self.doc.hr_approved_on = nowdate()
		elif self.new_state.lower() in ('Rejected'.lower(), 'Rejected By Supervisor'.lower()):
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Reject this request".format(self.doc.supervisor))
			self.doc.status = "Rejected"
		elif self.new_state.lower() == "Cancelled".lower():
			if self.doc.supervisor != frappe.session.user:
				frappe.throw("Only {} can Cancel this request".format(self.doc.supervisor))

	def overtime_application(self):
		if self.new_state.lower() in ("Draft".lower(), "Waiting Supervisor Approval".lower()):
			self.set_approver("Supervisor")
		elif self.new_state.lower() == "Waiting Approval".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.approver_name))
			self.set_approver("Department Head")
		elif self.new_state.lower() == "Approved".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Approve this request".format(self.doc.approver_name))
		elif self.new_state.lower() in ('Rejected'.lower(), 'Rejected By Supervisor'.lower()):
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Reject this request".format(self.doc.approver_name))
		elif self.new_state.lower() == "Cancelled".lower():
			if self.doc.approver != frappe.session.user:
				frappe.throw("Only {} can Cancel this request".format(self.doc.approver_name))

	def material_request(self):
		# needed so that non-employees like admin cannot create MR 
		# added by phuntsho on Feb 3 2021
		if not self.login_user: 
			frappe.throw("You do not have permission to create MR!")
		owner        = frappe.db.get_value("Employee", {"user_id": doc.owner}, ["user_id","employee_name","designation","name"])
		employee          = frappe.db.get_value("Employee", owner[3], ["user_id","employee_name","designation","name"])
		reports_to        = frappe.db.get_value("Employee", frappe.db.get_value("Employee", owner[3], "reports_to"), ["user_id","employee_name","designation","name"])

		if doc.approver and doc.approver != frappe.session.user:
			frappe.throw(_("Only the approver <b>{0}</b> allowed to verify or approve this document").format(doc.approver), title="Invalid Operation")

		if workflow_state == "Waiting Supervisor Approval".lower():
			if "MR GM" in frappe.get_roles(frappe.session.user): 
				# MR GM should be able to edit only if MR is submitted by Manager
				if (doc.owner != frappe.session.user) and "MR Manager" not in frappe.get_roles(doc.owner):
					frappe.throw("MR GM is not allowed to save the document during this workflow state.")
					
			officiating = get_officiating_employee(reports_to[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
			
			vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
			vars(doc)[document_approver[1]] = officiating[1] if officiating else reports_to[1]
			
		elif workflow_state == "Verified By Supervisor".lower():
			officiating = get_officiating_employee(final_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
			vars(doc)[document_approver[0]] = officiating[0] if officiating else final_approver[0]
			vars(doc)[document_approver[1]] = officiating[1] if officiating else final_approver[1]
		elif workflow_state == "Approved":
			doc.docstatus = 1

	def update_employment_status(self):
		emp_status = frappe.db.get_value("Leave Type", self.doc.leave_type, ["check_employment_status","employment_status"])
		if emp_status[0] and emp_status[1]:
			emp = frappe.get_doc("Employee", self.doc.employee)
			emp.employment_status = emp_status[1]
			emp.save(ignore_permissions=True)

	def set_approver(self, approver_type):
		if approver_type == "Supervisor":
			officiating = get_officiating_employee(self.reports_to[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.reports_to[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.reports_to[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.reports_to[2]
		elif approver_type == "HR":
			officiating = get_officiating_employee(self.hr_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.hr_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.hr_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.hr_approver[2]
		elif approver_type == "Department Head":
			officiating = get_officiating_employee(self.dept_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.dept_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.dept_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.dept_approver[2]
		elif approver_type == "CEO":
			officiating = get_officiating_employee(self.ceo[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.ceo[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.ceo[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.ceo[2]
		elif approver_type == "Final Approver":
			officiating = get_officiating_employee(self.final_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, self.field_list)
			vars(self.doc)[self.doc_approver[0]] = officiating[0] if officiating else self.final_approver[0]
			vars(self.doc)[self.doc_approver[1]] = officiating[1] if officiating else self.final_approver[1]
			vars(self.doc)[self.doc_approver[2]] = officiating[2] if officiating else self.final_approver[2]
		else:
			frappe.throw(_("Invalid approver type for Workflow"))

class NotifyCustomWorkflow:
	def __init__(self,doc):
		self.doc 			= doc
		self.old_state 		= self.doc.get_db_value("workflow_state")
		self.new_state 		= self.doc.workflow_state
		self.field_map 		= get_field_map()
		self.doc_approver	= self.field_map[self.doc.doctype]
		self.field_list		= ["user_id","employee_name","designation","name"]
		self.employee		= frappe.db.get_value("Employee", self.doc.employee, self.field_list)

	def notify_employee(self):
		employee = frappe.get_doc("Employee", self.doc.employee)
		if not employee.user_id:
			return

		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()

		if self.doc.doctype == "Leave Application":
			template = frappe.db.get_single_value('HR Settings', 'leave_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Leave Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Leave Encashment":
			template = frappe.db.get_single_value('HR Settings', 'encashment_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Encashment Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Salary Advance":
			template = frappe.db.get_single_value('HR Settings', 'advance_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Advance Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Travel Authorization":
			template = frappe.db.get_single_value('HR Settings', 'authorization_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Authorization Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Travel Claim":
			template = frappe.db.get_single_value('HR Settings', 'claim_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Claim Status Notification in HR Settings."))
				return
		elif self.doc.doctype == "Overtime Application":
			template = frappe.db.get_single_value('HR Settings', 'overtime_status_notification_template')
			if not template:
				frappe.msgprint(_("Please set default template for Overtime Status Notification in HR Settings."))
				return
		else:
			template = ""

		if not template:
			frappe.msgprint(_("Please set default template for {}.").format(self.doc.doctype))
			return
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response, args)

		self.notify({
			# for post in messages
			"message": message,
			"message_to": employee.user_id,
			# for email
			"subject": email_template.subject,
			"notify": "employee"
		})

	def notify_approver(self):
		if self.doc.get(self.doc_approver[0]):
			parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
			args = parent_doc.as_dict()

			if self.doc.doctype == "Leave Application":
				template = frappe.db.get_single_value('HR Settings', 'leave_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Leave Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Leave Encashment":
				template = frappe.db.get_single_value('HR Settings', 'encashment_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Encashment Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Salary Advance":
				template = frappe.db.get_single_value('HR Settings', 'advance_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Advance Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Travel Authorization":
				template = frappe.db.get_single_value('HR Settings', 'authorization_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Authorization Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Travel Claim":
				template = frappe.db.get_single_value('HR Settings', 'claim_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Claim Approval Notification in HR Settings."))
					return
			elif self.doc.doctype == "Overtime Application":
				template = frappe.db.get_single_value('HR Settings', 'overtime_approval_notification_template')
				if not template:
					frappe.msgprint(_("Please set default template for Overtime Approval Notification in HR Settings."))
					return
			else:
				template = ""

			if not template:
				frappe.msgprint(_("Please set default template for {}.").format(self.doc.doctype))
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response, args)

			self.notify({
				# for post in messages
				"message": message,
				"message_to": self.doc.get(self.doc_approver[0]),
				# for email
				"subject": email_template.subject
			})

	def notify(self, args):
		args = frappe._dict(args)
		# args -> message, message_to, subject

		contact = args.message_to
		if not isinstance(contact, list):
			if not args.notify == "employee":
				contact = frappe.get_doc('User', contact).email or contact

		sender      	    = dict()
		sender['email']     = frappe.get_doc('User', frappe.session.user).email
		sender['full_name'] = frappe.utils.get_fullname(sender['email'])

		try:
			frappe.sendmail(
				recipients = contact,
				sender = sender['email'],
				subject = args.subject,
				message = args.message,
			)
			frappe.msgprint(_("Email sent to {0}").format(contact))
		except frappe.OutgoingEmailError:
			pass

	def send_notification(self):
		#frappe.msgprint(_("old_state: {}, new_state: {}").format(self.old_state, self.new_state))
		if self.new_state == "Draft":
			return
		elif self.new_state in ("Approved", "Rejected", "Cancelled"):
			self.notify_employee()
		elif self.new_state.startswith("Waiting") and self.old_state != self.new_state:
			self.notify_approver()
		else:
			frappe.msgprint(_("Email notifications not configured for workflow state {}").format(self.new_state))

def get_field_map():
	return {
		"Salary Advance": ["advance_approver","advance_approver_name","advance_approver_designation"],
		"Leave Encashment": ["approver","approver_name","approver_designation"],
		"Leave Application": ["leave_approver", "leave_approver_name", "leave_approver_designation"],
		"Travel Authorization": ["supervisor", "supervisor_name", "supervisor_designation"],
		"Travel Claim": ["supervisor", "supervisor_name", "supervisor_designation"],
		"Overtime Application": ["approver", "approver_name", "approver_designation"],
	}

def validate_workflow_states(doc):
	wf = CustomWorkflow(doc)
	wf.apply_workflow()

def notify_workflow_states(doc):
	wf = NotifyCustomWorkflow(doc)
	wf.send_notification()
