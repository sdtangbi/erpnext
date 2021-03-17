# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import cint, getdate, validate_email_address, today, add_years, format_datetime, cstr, flt, nowdate, date_diff, add_days
from frappe.model.naming import set_name_by_naming_series
from frappe import throw, _, scrub
from frappe.permissions import add_user_permission, remove_user_permission, \
	set_user_permission_if_allowed, has_permission
from frappe.model.document import Document
from erpnext.utilities.transaction_base import delete_events
from frappe.utils.nestedset import NestedSet
from erpnext.hr.doctype.job_offer.job_offer import get_staffing_plan_detail
from erpnext.custom_utils import get_year_start_date, get_year_end_date, round5, check_future_date

class EmployeeUserDisabledError(frappe.ValidationError): pass
class EmployeeLeftValidationError(frappe.ValidationError): pass

class Employee(NestedSet):
	nsm_parent_field = 'reports_to'

	def autoname(self):
		naming_method = frappe.db.get_value("HR Settings", None, "emp_created_by")
		if not naming_method:
			throw(_("Please setup Employee Naming System in Human Resource > HR Settings"))
		else:
			if naming_method == 'Naming Series':
				set_name_by_naming_series(self)
			elif naming_method == 'Employee Number':
				self.name = self.employee_number
			elif naming_method == 'Full Name':
				self.set_employee_name()
				self.name = self.employee_name

		self.employee = self.name

	def validate(self):
		from erpnext.controllers.status_updater import validate_status
		validate_status(self.status, ["Active", "Temporary Leave", "Left"])

		self.employee = self.name
		self.set_employee_name()
		self.validate_date()
		self.validate_email()
		self.validate_status()
		self.validate_reports_to()
		self.validate_preferred_email()
		if self.job_applicant:
			self.validate_onboarding_process()

		if self.user_id:
			self.validate_user_details()
		else:
			existing_user_id = frappe.db.get_value("Employee", self.name, "user_id")
			if existing_user_id:
				remove_user_permission(
					"Employee", self.name, existing_user_id)

		''' Ver.20200915.01 Begins, following code added by SHIV on 2020/09/15 '''
		self.update_cost_center()
		# Following method introduced by SHIV on 04/10/2017
		self.populate_work_history()
		# Following method introduced by SHIV on 15/08/2018
		self.populate_family_details()
		# Following method introduced by SHIV on 08/04/2019
		self.update_retirement_age()
		''' Ver.20200915.01 Ends '''

	# Following method introducted by SHIV on 04/10/2017
	def populate_work_history(self):
			return
			if not self.internal_work_history:
					self.append("internal_work_history",{
											"branch": self.branch,
											"cost_center": self.cost_center,
											"business_activity": self.business_activity,
											"department": self.department,
											"designation": self.designation,
											"from_date": self.date_of_joining,
											"owner": frappe.session.user,
											"creation": nowdate(),
											"modified_by": frappe.session.user,
											"modified": nowdate()
					})
			else:
					# Fetching previous document from db
					prev_doc = frappe.get_doc(self.doctype,self.name)
					self.date_of_transfer = self.date_of_transfer if self.date_of_transfer else today()

					if (getdate(self.date_of_joining) != prev_doc.date_of_joining) or \
						(self.status == 'Left' and self.relieving_date) or \
						(self.cost_center != prev_doc.cost_center) or \
						(self.designation != prev_doc.designation):
							for wh in self.internal_work_history:
									# For change in date_of_joining
									if (getdate(self.date_of_joining) != prev_doc.date_of_joining):
											if (getdate(prev_doc.date_of_joining) == getdate(wh.from_date)):
													wh.from_date = self.date_of_joining

									# For change in relieving_date, cost_center
									if (self.status == 'Left' and self.relieving_date):
											if not wh.to_date:
													wh.to_date = self.relieving_date
											elif prev_doc.relieving_date:
													if (getdate(prev_doc.relieving_date) == getdate(wh.to_date)):
															wh.to_date = self.relieving_date
									elif (self.cost_center != prev_doc.cost_center) or \
											(self.designation != prev_doc.designation):
											if getdate(self.date_of_transfer) > getdate(today()):
													frappe.throw(_("Date of transfer cannot be a future date."),title="Invalid Date")      
											elif not wh.to_date:
													if getdate(self.date_of_transfer) < getdate(wh.from_date):
															frappe.throw(_("Row#{0} : Date of transfer({1}) cannot be beyond current effective entry.").format(wh.idx,self.date_of_transfer),title="Invalid Date")
															
													wh.to_date = wh.from_date if add_days(getdate(self.date_of_transfer),-1) < getdate(wh.from_date) else add_days(self.date_of_transfer,-1)
											
					if (self.cost_center != prev_doc.cost_center) or \
						(self.designation != prev_doc.designation):
							self.append("internal_work_history",{
										"branch": self.branch,
										"cost_center": self.cost_center,
										"business_activity": self.business_activity,
										"department": self.department,
										"designation": self.designation,
										"from_date": self.date_of_transfer,
										"owner": frappe.session.user,
										"creation": nowdate(),
										"modified_by": frappe.session.user,
										"modified": nowdate()
							})
					elif not self.internal_work_history:
							self.append("internal_work_history",{
										"branch": self.branch,
										"cost_center": self.cost_center,
										"business_activity": self.business_activity,
										"department": self.department,
										"designation": self.designation,
										"from_date": self.date_of_joining,
										"owner": frappe.session.user,
										"creation": nowdate(),
										"modified_by": frappe.session.user,
										"modified": nowdate()
							})

	def populate_family_details(self):
			exists = sum(1 if i.relationship == "Self" else 0 for i in self.employee_family_details)
			#if not self.employee_family_details or not frappe.db.exists("Employee Family Details", {"parent": self.name, "relationship": "Self"}):
			if not exists:
				self.append("employee_family_details",{
							"relationship": "Self",
							"full_name": self.employee_name,
							"gender": self.gender,
							"date_of_birth": self.date_of_birth,
							"cid_no": self.passport_number,
							"district_name": self.dzongkhag,
							"city_name": self.gewog,
							"village_name": self.village,
							"owner": frappe.session.user,
							"creation": nowdate(),
							"modified_by": frappe.session.user,
							"modified": nowdate()
				})
			else:
				if exists > 1:
					frappe.throw(_("Multiple entries for Self ({0} {1}) not permitted under family details.").format(self.name, self.employee_name), title="Duplicate Entry Found")
				else:
						for f in self.employee_family_details:
							if f.relationship == "Self":
								f.full_name     = self.employee_name
								f.gender        = self.gender
								f.date_of_birth = self.date_of_birth
								f.cid_no        = self.passport_number

	def update_retirement_age(self):
		ret = frappe.db.sql("""
						select date_add('{0}', INTERVAL retirement_age YEAR) as date_of_retirement
						from `tabEmployee Group` where name = '{1}'
		""".format(getdate(self.date_of_birth), self.employee_group), as_dict=True)
		if ret:
				self.date_of_retirement = ret[0].date_of_retirement

	# Ver.20200915.01, method update_cost_center created by SHIV on 2020/09/15
	def update_cost_center(self):
		if self.branch:
			self.gis_policy_number = frappe.db.get_value("Branch", self.branch, "gis_policy_number")
			self.cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")

	def set_employee_name(self):
		self.employee_name = ' '.join(filter(lambda x: x, [self.first_name, self.middle_name, self.last_name]))

	def validate_user_details(self):
		data = frappe.db.get_value('User',
			self.user_id, ['enabled', 'user_image'], as_dict=1)
		if data.get("user_image"):
			self.image = data.get("user_image")
		self.validate_for_enabled_user_id(data.get("enabled", 0))
		self.validate_duplicate_user_id()

	def update_nsm_model(self):
		frappe.utils.nestedset.update_nsm(self)

	def on_update(self):
		self.update_nsm_model()
		if self.user_id:
			self.update_user()
			self.update_user_permissions()
		self.reset_employee_emails_cache()
		''' Ver.20200918 Begins '''
		# Following methods added by SHIV on 2020/09/18
		self.post_casual_leave()
		self.update_salary_structure()
		''' Ver.20200918 Ends '''

	# Following method added by SHIV on 2020/09/18
	def post_casual_leave(self):
		from_date = getdate(self.date_of_joining)
		to_date = get_year_end_date(from_date)

		if not cint(self.casual_leave_allocated):
			if frappe.db.exists("Leave Allocation", {"leave_type": "Casual Leave", "employee": self.name, "from_date": ("<=",str(to_date)), "to_date": (">=", str(from_date))}):
				self.add_comments("Auto allocation of CL is skipped as an allocation already exists for the period {} - {}".format(from_date, to_date))
				self.db_set("casual_leave_allocated", 1)
				return
				
			if not frappe.db.sql("""select count(*) as counts from `tabFiscal Year` where now() between year_start_date and year_end_date
				and '{}' <= year_end_date and '{}' >= year_start_date""".format(from_date, to_date))[0][0]:
				self.add_comments("Auto allocation of CL is skipped as the Employee's Date of Joing is not in current Fiscal Year")
				self.db_set("casual_leave_allocated", 1)
				return

			credits_per_year = frappe.db.get_value("Employee Group Item", {"parent": self.employee_group, "leave_type": 'Casual Leave'}, "credits_per_year")
			if flt(credits_per_year):
				no_of_months = frappe.db.sql("""
						select (
								case
										when day('{0}') > 1 and day('{0}') <= 15
										then timestampdiff(MONTH,'{0}','{1}')+1
										else timestampdiff(MONTH,'{0}','{1}')
								end
								) as no_of_months
				""".format(str(self.date_of_joining),str(add_days(to_date,1))))[0][0]

				new_leaves_allocated = round5((flt(no_of_months)/12)*flt(credits_per_year))
				new_leaves_allocated = new_leaves_allocated if new_leaves_allocated <= flt(credits_per_year) else flt(credits_per_year)

				if flt(new_leaves_allocated):
						la = frappe.new_doc("Leave Allocation")
						la.employee = self.employee
						la.employee_name = self.employee_name
						la.leave_type = "Casual Leave"
						la.from_date = str(from_date)
						la.to_date = str(to_date)
						la.carry_forward = cint(0)
						la.new_leaves_allocated = flt(new_leaves_allocated)
						la.submit()
						self.db_set("casual_leave_allocated", 1)

	# Following method added by SHIV on 2020/09/18
	def update_salary_structure(self):
		ss = frappe.db.get_value("Salary Structure", {"employee": self.name, "is_active": "Yes"}, "name")
		if ss:
			doc = frappe.get_doc("Salary Structure", ss)
			doc.flags.ignore_permissions = 1
			doc.save()

	# Following method created by SHIV on 2020/09/18
	def add_comments(self, msg):
		doc = frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": self.doctype,
			"reference_name": self.name,
			"content": msg
		}).save()

	def update_user_permissions(self):
		''' Ver.20200921 Begins '''
		# Following line commented and the subsequent added by SHIV on 2020/09/21
		#if not self.create_user_permission: return
		if self.user_id and not self.create_user_permission:
			remove_user_permission("Employee", self.name, self.user_id)
			return
		''' Ver.20200921 Ends '''

		if not has_permission('User Permission', ptype='write', raise_exception=False): return

		employee_user_permission_exists = frappe.db.exists('User Permission', {
			'allow': 'Employee',
			'for_value': self.name,
			'user': self.user_id
		})

		if employee_user_permission_exists: return

		# Following code is commented by SHIV on 2020/09/19 as it is duplication
		'''
		employee_user_permission_exists = frappe.db.exists('User Permission', {
			'allow': 'Employee',
			'for_value': self.name,
			'user': self.user_id
		})

		if employee_user_permission_exists: return
		'''

		add_user_permission("Employee", self.name, self.user_id)
		set_user_permission_if_allowed("Company", self.company, self.user_id)

	def update_user(self):
		# add employee role if missing
		user = frappe.get_doc("User", self.user_id)
		user.flags.ignore_permissions = True

		if "Employee" not in user.get("roles"):
			user.append_roles("Employee")

		# copy details like Fullname, DOB and Image to User
		if self.employee_name and not (user.first_name and user.last_name):
			employee_name = self.employee_name.split(" ")
			if len(employee_name) >= 3:
				user.last_name = " ".join(employee_name[2:])
				user.middle_name = employee_name[1]
			elif len(employee_name) == 2:
				user.last_name = employee_name[1]

			user.first_name = employee_name[0]

		if self.date_of_birth:
			user.birth_date = self.date_of_birth

		if self.gender:
			user.gender = self.gender

		if self.image:
			if not user.user_image:
				user.user_image = self.image
				try:
					frappe.get_doc({
						"doctype": "File",
						"file_name": self.image,
						"attached_to_doctype": "User",
						"attached_to_name": self.user_id
					}).insert()
				except frappe.DuplicateEntryError:
					# already exists
					pass

		user.save()

	def validate_date(self):
		if self.date_of_birth and getdate(self.date_of_birth) > getdate(today()):
			throw(_("Date of Birth cannot be greater than today."))

		if self.date_of_birth and self.date_of_joining and getdate(self.date_of_birth) >= getdate(self.date_of_joining):
			throw(_("Date of Joining must be greater than Date of Birth"))

		elif self.date_of_retirement and self.date_of_joining and (getdate(self.date_of_retirement) <= getdate(self.date_of_joining)):
			throw(_("Date Of Retirement must be greater than Date of Joining"))

		elif self.relieving_date and self.date_of_joining and (getdate(self.relieving_date) <= getdate(self.date_of_joining)):
			throw(_("Relieving Date must be greater than Date of Joining"))

		elif self.contract_end_date and self.date_of_joining and (getdate(self.contract_end_date) <= getdate(self.date_of_joining)):
			throw(_("Contract End Date must be greater than Date of Joining"))

	def validate_email(self):
		if self.company_email:
			validate_email_address(self.company_email, True)
		if self.personal_email:
			validate_email_address(self.personal_email, True)

	def validate_status(self):
		if self.status == 'Left':
			reports_to = frappe.db.get_all('Employee',
				filters={'reports_to': self.name, 'status': "Active"},
				fields=['name','employee_name']
			)
			if reports_to:
				link_to_employees = [frappe.utils.get_link_to_form('Employee', employee.name, label=employee.employee_name) for employee in reports_to]
				throw(_("Employee status cannot be set to 'Left' as following employees are currently reporting to this employee:&nbsp;")
					+ ', '.join(link_to_employees), EmployeeLeftValidationError)
			if not self.relieving_date:
				throw(_("Please enter relieving date."))

	def validate_for_enabled_user_id(self, enabled):
		if not self.status == 'Active':
			return

		if enabled is None:
			frappe.throw(_("User {0} does not exist").format(self.user_id))
		if enabled == 0:
			frappe.throw(_("User {0} is disabled").format(self.user_id), EmployeeUserDisabledError)

	def validate_duplicate_user_id(self):
		employee = frappe.db.sql_list("""select name from `tabEmployee` where
			user_id=%s and status='Active' and name!=%s""", (self.user_id, self.name))
		if employee:
			throw(_("User {0} is already assigned to Employee {1}").format(
				self.user_id, employee[0]), frappe.DuplicateEntryError)

	def validate_reports_to(self):
		if self.reports_to == self.name:
			throw(_("Employee cannot report to himself."))

	def on_trash(self):
		self.update_nsm_model()
		delete_events(self.doctype, self.name)
		if frappe.db.exists("Employee Transfer", {'new_employee_id': self.name, 'docstatus': 1}):
			emp_transfer = frappe.get_doc("Employee Transfer", {'new_employee_id': self.name, 'docstatus': 1})
			emp_transfer.db_set("new_employee_id", '')

	def validate_preferred_email(self):
		if self.prefered_contact_email and not self.get(scrub(self.prefered_contact_email)):
			frappe.msgprint(_("Please enter " + self.prefered_contact_email))

	def validate_onboarding_process(self):
		employee_onboarding = frappe.get_all("Employee Onboarding",
			filters={"job_applicant": self.job_applicant, "docstatus": 1, "boarding_status": ("!=", "Completed")})
		if employee_onboarding:
			doc = frappe.get_doc("Employee Onboarding", employee_onboarding[0].name)
			doc.validate_employee_creation()
			doc.db_set("employee", self.name)

	def reset_employee_emails_cache(self):
		prev_doc = self.get_doc_before_save() or {}
		cell_number = cstr(self.get('cell_number'))
		prev_number = cstr(prev_doc.get('cell_number'))
		if (cell_number != prev_number or
			self.get('user_id') != prev_doc.get('user_id')):
			frappe.cache().hdel('employees_with_number', cell_number)
			frappe.cache().hdel('employees_with_number', prev_number)

def get_timeline_data(doctype, name):
	'''Return timeline for attendance'''
	return dict(frappe.db.sql('''select unix_timestamp(attendance_date), count(*)
		from `tabAttendance` where employee=%s
			and attendance_date > date_sub(curdate(), interval 1 year)
			and status in ('Present', 'Half Day')
			group by attendance_date''', name))

@frappe.whitelist()
#def get_retirement_date(date_of_birth=None):
def get_retirement_date(date_of_birth=None, employee_group=None):
	''' Ver.20200914.01 Begins, following code commented by SHIV on 2020/09/14 '''
	'''
	ret = {}
	if date_of_birth:
		try:
			retirement_age = int(frappe.db.get_single_value("HR Settings", "retirement_age") or 60)
			dt = add_years(getdate(date_of_birth),retirement_age)
			ret = {'date_of_retirement': dt.strftime('%Y-%m-%d')}
		except ValueError:
			# invalid date
			ret = {}

	return ret
	'''
	''' Ver.20200914.01 Ends '''

	''' Ver.20200914.01 Beings, following code added by SHIV on 2020/09/14 '''
	import datetime
	ret = {}
	if date_of_birth and employee_group:
		try:
			retirement_age = int(frappe.db.get_value("Employee Group", employee_group, "retirement_age"))					
			dt = add_years(getdate(date_of_birth),retirement_age)
			ret = {'date_of_retirement': dt.strftime('%Y-%m-%d')}
		except ValueError:
			# invalid date
			ret = {}

	return ret
	''' Ver.20200914.01 Ends '''
	
def validate_employee_role(doc, method):
	# called via User hook
	if "Employee" in [d.role for d in doc.get("roles")]:
		if not frappe.db.get_value("Employee", {"user_id": doc.name}):
			frappe.msgprint(_("Please set User ID field in an Employee record to set Employee Role"))
			doc.get("roles").remove(doc.get("roles", {"role": "Employee"})[0])

def update_user_permissions(doc, method):
	# called via User hook
	if "Employee" in [d.role for d in doc.get("roles")]:
		if not has_permission('User Permission', ptype='write', raise_exception=False): return
		employee = frappe.get_doc("Employee", {"user_id": doc.name})
		employee.update_user_permissions()

def send_birthday_reminders():
	"""Send Employee birthday reminders if no 'Stop Birthday Reminders' is not set."""
	if int(frappe.db.get_single_value("HR Settings", "stop_birthday_reminders") or 0):
		return

	birthdays = get_employees_who_are_born_today()

	if birthdays:
		employee_list = frappe.get_all('Employee',
			fields=['name','employee_name'],
			filters={'status': 'Active',
				'company': birthdays[0]['company']
		 	}
		)
		employee_emails = get_employee_emails(employee_list)
		birthday_names = [name["employee_name"] for name in birthdays]
		birthday_emails = [email["user_id"] or email["personal_email"] or email["company_email"] for email in birthdays]

		birthdays.append({'company_email': '','employee_name': '','personal_email': '','user_id': ''})

		for e in birthdays:
			if e['company_email'] or e['personal_email'] or e['user_id']:
				if len(birthday_names) == 1:
					continue
				recipients = e['company_email'] or e['personal_email'] or e['user_id']


			else:
				recipients = list(set(employee_emails) - set(birthday_emails))

			frappe.sendmail(recipients=recipients,
				subject=_("Birthday Reminder"),
				message=get_birthday_reminder_message(e, birthday_names),
				header=['Birthday Reminder', 'green'],
			)

def get_birthday_reminder_message(employee, employee_names):
	"""Get employee birthday reminder message"""
	pattern = "</Li><Br><Li>"
	message = pattern.join(filter(lambda u: u not in (employee['employee_name']), employee_names))
	message = message.title()

	if pattern not in message:
		message = "Today is {0}'s birthday \U0001F603".format(message)

	else:
		message = "Today your colleagues are celebrating their birthdays \U0001F382<br><ul><strong><li> " + message +"</li></strong></ul>"

	return message


def get_employees_who_are_born_today():
	"""Get Employee properties whose birthday is today."""
	return frappe.db.get_values("Employee",
		fieldname=["name", "personal_email", "company", "company_email", "user_id", "employee_name"],
		filters={
			"date_of_birth": ("like", "%{}".format(format_datetime(getdate(), "-MM-dd"))),
			"status": "Active",
		},
		as_dict=True
	)


def get_holiday_list_for_employee(employee, raise_exception=True):
	if employee:
		holiday_list, company = frappe.db.get_value("Employee", employee, ["holiday_list", "company"])
	else:
		holiday_list=''
		company=frappe.db.get_value("Global Defaults", None, "default_company")

	if not holiday_list:
		holiday_list = frappe.get_cached_value('Company',  company,  "default_holiday_list")

	if not holiday_list and raise_exception:
		frappe.throw(_('Please set a default Holiday List for Employee {0} or Company {1}').format(employee, company))

	return holiday_list

def is_holiday(employee, date=None, raise_exception=True):
	'''Returns True if given Employee has an holiday on the given date
	:param employee: Employee `name`
	:param date: Date to check. Will check for today if None'''

	holiday_list = get_holiday_list_for_employee(employee, raise_exception)
	if not date:
		date = today()

	if holiday_list:
		return frappe.get_all('Holiday List', dict(name=holiday_list, holiday_date=date)) and True or False

@frappe.whitelist()
def deactivate_sales_person(status = None, employee = None):
	if status == "Left":
		sales_person = frappe.db.get_value("Sales Person", {"Employee": employee})
		if sales_person:
			frappe.db.set_value("Sales Person", sales_person, "enabled", 0)

@frappe.whitelist()
def create_user(employee, user = None, email=None):
	emp = frappe.get_doc("Employee", employee)

	employee_name = emp.employee_name.split(" ")
	middle_name = last_name = ""

	if len(employee_name) >= 3:
		last_name = " ".join(employee_name[2:])
		middle_name = employee_name[1]
	elif len(employee_name) == 2:
		last_name = employee_name[1]

	first_name = employee_name[0]

	if email:
		emp.prefered_email = email

	user = frappe.new_doc("User")
	user.update({
		"name": emp.employee_name,
		"email": emp.prefered_email,
		"enabled": 1,
		"first_name": first_name,
		"middle_name": middle_name,
		"last_name": last_name,
		"gender": emp.gender,
		"birth_date": emp.date_of_birth,
		"phone": emp.cell_number,
		"bio": emp.bio
	})
	user.insert()
	return user.name

def get_employee_emails(employee_list):
	'''Returns list of employee emails either based on user_id or company_email'''
	employee_emails = []
	for employee in employee_list:
		if not employee:
			continue
		user, company_email, personal_email = frappe.db.get_value('Employee', employee,
											['user_id', 'company_email', 'personal_email'])
		email = user or company_email or personal_email
		if email:
			employee_emails.append(email)
	return employee_emails

@frappe.whitelist()
def get_children(doctype, parent=None, company=None, is_root=False, is_tree=False):
	filters = [['company', '=', company]]
	fields = ['name as value', 'employee_name as title']

	if is_root:
		parent = ''
	if parent and company and parent!=company:
		filters.append(['reports_to', '=', parent])
	else:
		filters.append(['reports_to', '=', ''])

	employees = frappe.get_list(doctype, fields=fields,
		filters=filters, order_by='name')

	for employee in employees:
		is_expandable = frappe.get_all(doctype, filters=[
			['reports_to', '=', employee.get('value')]
		])
		employee.expandable = 1 if is_expandable else 0

	return employees


def on_doctype_update():
	frappe.db.add_index("Employee", ["lft", "rgt"])

def has_user_permission_for_employee(user_name, employee_name):
	return frappe.db.exists({
		'doctype': 'User Permission',
		'user': user_name,
		'allow': 'Employee',
		'for_value': employee_name
	})

''' Ver.20200914, method get_employee_groups added by SHIV on 2020/09/14(from NRDCL) '''
def get_employee_groups(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select employee_group
			from `tabEmployment Type Item`
			where parent = '{0}'
			""".format(filters.get("employment_type")))

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if "HR User" in user_roles or "HR Manager" in user_roles:
		return
	else:
		return """(
			exists(select 1
				from `tabEmployee` as e
				where e.name = `tabEmployee`.name
				and e.user_id = '{user}')
		)""".format(user=user)

# Following code added by SHIV on 2020/09/21
def has_record_permission(doc, user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if "HR User" in user_roles or "HR Manager" in user_roles:
		return True
	else:			
		if frappe.db.exists("Employee", {"name":doc.name, "user_id": user}):
			return True
		else:
			return False 

	return True

# Following code moved from NRDCL by SHIV on 2020/10/05
@frappe.whitelist()
def get_overtime_rate(employee):
	basic = frappe.db.sql("select b.eligible_for_overtime_and_payment, a.amount as basic_pay from `tabSalary Detail` a, `tabSalary Structure` b where a.parent = b.name and a.salary_component = 'Basic Pay' and b.is_active = 'Yes' and b.employee = \'" + str(employee) + "\'", as_dict=True)
	if basic:
			if not cint(basic[0].eligible_for_overtime_and_payment):
				if not frappe.db.get_value("Employee Grade", frappe.db.get_value("Employee", employee, "grade"), "eligible_for_overtime"):
					frappe.throw(_("Employee is not eligible for Overtime"))

			return ((flt(basic[0].basic_pay) * 1.5) / (30 * 8))
	else:
			frappe.throw("No Salary Structure found for the employee")
