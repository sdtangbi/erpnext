from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Employee"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Employment Type",
				},
				{
					"type": "doctype",
					"name": "Branch",
				},
				{
					"type": "doctype",
					"name": "Department",
				},
				{
					"type": "doctype",
					"name": "Designation",
				},
				{
					"type": "doctype",
					"name": "Employee Grade",
				},
				{
					"type": "doctype",
					"name": "Employee Group",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Health Insurance"
				},
				{
					"type": "doctype",
					"name": "Officiating Employee"
				},
			]
		},
		{
			"label": _("Attendance"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Attendance Tool",
					"hide_count": True,
					"onboard": 1,
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Attendance",
					"onboard": 1,
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Attendance Request",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Upload Attendance",
					"hide_count": True,
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Checkin",
					"hide_count": True,
					"dependencies": ["Employee"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Monthly Attendance Sheet",
					"doctype": "Attendance"
				},
				{
					"type": "doctype",
					"name": "Overtime Application",
					"hide_count": True,
					"onboard": 1,
					"dependencies": ["Employee"]
				}
				
			]
		},
		{
			"label": _("Leaves"),
			"items": [
				{
					"type": "doctype",
					"name": "Leave Application",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Leave Allocation",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Leave Policy",
					"dependencies": ["Leave Type"]
				},
				{
					"type": "doctype",
					"name": "Leave Period",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name":"Leave Type",
				},
				{
					"type": "doctype",
					"name": "Holiday List",
				},
				{
					"type": "doctype",
					"name": "Compensatory Leave Request",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Leave Encashment",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Leave Block List",
				},
				{
					"type": "doctype",
					"name": "Merge CL To EL",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Employee Leave Balance",
					"doctype": "Leave Application"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Leave Ledger Entry",
					"doctype": "Leave Ledger Entry"
				},
			]
		},
		{
			"label": _("Payroll"),
			"items": [
				{
					"type": "doctype",
					"name": "Salary Structure",
					"onboard": 1,
				},
				# Following code is commented by SHIV on 2020/09/18
				#{
				#	"type": "doctype",
				#	"name": "Salary Structure Assignment",
				#	"onboard": 1,
				#	"dependencies": ["Salary Structure", "Employee"],
				#},
				
				{
					"type": "doctype",
					"name": "Payroll Entry",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Salary Slip",
					"onboard": 1,
				},
				# Following code is commented by SHIV on 2020/09/18
				#{
				#	"type": "doctype",
				#	"name": "Payroll Period",
				#},
				#{
				#	"type": "doctype",
				#	"name": "Income Tax Slab",
				#},
				{
					"type": "doctype",
					"name": "Salary Tax",
				},
				{
					"type": "doctype",
					"name": "Salary Component",
				},
				{
					"type": "doctype",
					"name": "Additional Salary",
				},
				{
					"type": "doctype",
					"name": "Retention Bonus",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Incentive",
					"dependencies": ["Employee"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Salary Register",
					"doctype": "Salary Slip"
				},
			]
		},
		{
			"label": _("Salary Increment"),
			"items": [
				{
					"type": "doctype",
					"name": "Increment Entry",
					"onboard": 1,
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Salary Increment",
					"onboard": 1,
					"dependencies": ["Employee"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"label": "Salary Increment Report",
					"name": "Salary Increment",
					"doctype": "Salary Increment"
				},
			]
		},
		{
			"label": _("Salary Advance"),
			"items": [
				{
					"type": "doctype",
					"name": "Salary Advance",
					"onboard": 1,
					"dependencies": ["Employee"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"label": "Salary Advance Report",
					"name": "Salary Advance Report",
					"doctype": "Salary Advance"
				},
			]
		},
		#added by cheten on 4/3/2021
		{
			"label": _("MR Management"),
			"items": [
				{
					"type": "doctype",
					"name": "Muster Roll Employee",
					"onboard": 1,
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "MusterRoll Application",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Upload Attendance Others",
					"onboard": 1,
					"label": "Upload Bulk Attendance for MR"
				},
				{
					"type": "doctype",
					"name": "Process MR Payment",
					"onboard": 1,
					"label": "Process Payment for MR"
				},
				{
					"type": "doctype",
					"name": "Upload Overtime Entries",
					"label": "Upload Overtime Entries for MR",
					"onboard": 1
				},
				# {
				# 	"type": "report",
				# 	"name": "Overtime Register",
				# 	"label": "Overtime Register for MR",
				# 	"onboard": 1,
				# 	"doctype": "Overtime Application"
				# }
			]
		},
		#end
		{
			"label": _("Employee Tax and Benefits"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Tax Exemption Declaration",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Tax Exemption Proof Submission",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Other Income",
				},
				{
					"type": "doctype",
					"name": "Employee Benefit Application",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Benefit Claim",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Tax Exemption Category",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Tax Exemption Sub Category",
					"dependencies": ["Employee"]
				},
			]
		},
		{
			"label": _("Employee Lifecycle"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee Onboarding",
					"dependencies": ["Job Applicant"],
				},
				{
					"type": "doctype",
					"name": "Employee Skill Map",
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Employee Promotion",
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Employee Transfer",
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Employee Separation",
					"dependencies": ["Employee"],
				},
				{
					"type": "doctype",
					"name": "Employee Onboarding Template",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Separation Template",
					"dependencies": ["Employee"]
				},
			]
		},
		{
			"label": _("Recruitment"),
			"items": [
				{
					"type": "doctype",
					"name": "Job Opening",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Job Applicant",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Job Offer",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Staffing Plan",
				},
			]
		},
		{
			"label": _("Training"),
			"items": [
				{
					"type": "doctype",
					"name": "Training Program"
				},
				{
					"type": "doctype",
					"name": "Training Event"
				},
				{
					"type": "doctype",
					"name": "Training Result"
				},
				{
					"type": "doctype",
					"name": "Training Feedback"
				},
			]
		},
		{
			"label": _("Performance"),
			"items": [
				{
					"type": "doctype",
					"name": "Appraisal",
				},
				{
					"type": "doctype",
					"name": "Appraisal Template",
				},
				{
					"type": "doctype",
					"name": "Energy Point Rule",
				},
				{
					"type": "doctype",
					"name": "Energy Point Log",
				},
				{
					"type": "link",
					"doctype": "Energy Point Log",
					"label": _("Energy Point Leaderboard"),
					"route": "#social/users"
				},
			]
		},
		{
			"label": _("Travel"),
			"items": [
				{
					"type": "doctype",
					"name": "Travel Authorization",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Travel Claim",
					"dependencies": ["Employee"]
				},
			]
		},
		{
			"label": _("Expense Claims"),
			"items": [
				{
					"type": "doctype",
					"name": "Expense Claim",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Employee Advance",
					"dependencies": ["Employee"]
				},
			]
		},
		{
			"label": _("Leadership Feedback"),
			"items": [
				{
					"type": "doctype",
					"name": "Competency",
				},
				{
					"type": "doctype",
					"name": "Competency Detail",
				},
				{
					"type": "doctype",
					"name": "Feedback Rating",
				},
				{
					"type": "doctype",
					"name": "Feedback Recipient Settings"
				},
				{
					"type": "doctype",
					"name": "Feedback"
				},
			]
		},
		{
			"label": _("Loans"),
			"items": [
				{
					"type": "doctype",
					"name": "Loan Application",
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Loan"
				},
				{
					"type": "doctype",
					"name": "Loan Type",
				},
			]
		},
		{
			"label": _("Shift Management"),
			"items": [
				{
					"type": "doctype",
					"name": "Shift Type",
				},
				{
					"type": "doctype",
					"name": "Shift Request",
				},
				{
					"type": "doctype",
					"name": "Shift Assignment",
				},
			]
		},
		{
			"label": _("Fleet Management"),
			"items": [
				{
					"type": "doctype",
					"name": "Vehicle"
				},
				{
					"type": "doctype",
					"name": "Vehicle Log"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Vehicle Expenses",
					"doctype": "Vehicle"
				},
			]
		},
		{
			"label": _("Settings"),
			"icon": "fa fa-cog",
			"items": [
				{
					"type": "doctype",
					"name": "HR Settings",
				},
				{
					"type": "doctype",
					"name": "Daily Work Summary Group"
				},
				{
					"type": "page",
					"name": "team-updates",
					"label": _("Team Updates")
				},
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Employee Birthday",
					"doctype": "Employee"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Employees working on a holiday",
					"doctype": "Employee"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Department Analytics",
					"doctype": "Employee"
				},
				# following added by Cheten on 3/11/2020
				{
                    "type": "report",
                    "is_query_report": True,
                    "name": "Feedback Received",
                    "doctype": "Feedback"
                },
				#end
				# following added by SHIV on 2020/09/16
				{
					"type": "report",
					"is_query_report": True,
					"name": "Employee Salary Structure",
					"doctype": "Salary Structure"
				},
				
				{
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Leave Encashment Report",
                                        "label": _("Leave Encashment Report"),
                                        "doctype": "Leave Encashment"
                                },
                                {
                                        "type": "report",
                                        "name": "Employee Information",
                                        "doctype": "Employee"
                                },
				{
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Monthly Attendance Sheet",
                                        "doctype": "Attendance"
                                },
				{
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Overtime Register",
                                        "doctype": "Attendance"
                                },
				{
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Salary Tax Report",
                                        "label": "RRCO Tax Slab Details",
                                        "doctype": "Salary Tax"
                                },
                                {
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Employee Due Date Report",
                                        "doctype": "Employee"
                                },
				{
                                    "type": "report",
                                    "is_query_report": True,
                                    "name": "Travel Report",
                                    "doctype": "Travel Claim"
                                },
                                {
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Salary Advance Report",
                                        "doctype": "Salary Advance"
                                }
			]
		},
		{
			"label": _("Salary Reports"),
			"icon": "fa fa-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Monthly Salary Register",
					"doctype": "Salary Slip"
				},
				{
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Loan Report",
                                        "label": _("Loan Report"),
                                        "doctype": "Salary Slip"
                                },
                                {
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "SSS Report",
                                        "label": _("Salary Saving Scheme Report"),
                                        "doctype": "Salary Slip"
                                },
                                {
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "PF Report",
                                        "label": _("PF Report"),
                                        "doctype": "Salary Slip"
                                },
				{
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "GIS Report",
                                        "label": _("GIS Report"),
                                        "doctype": "Salary Slip"
                                },
                                {
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Tax and Health Report",
                                        "label": _("Salary Tax & Health Contribution Report"),
                                        "doctype": "Salary Slip"
                                },
                                {
                                        "type": "report",
                                        "is_query_report": True,
                                        "name": "Earning Report",
                                        "doctype": "Salary Slip"
                                },
				{
                                        "type" : "report",
                                        "is_query_report": True,
                                        "name": "Salary Payable Report",
                                        "label": _("Salary Payable Report"),
                                        "doctype": "Salary Slip"
                                },
                                {
                                        "type" : "report",
                                        "is_query_report": True,
                                        "name": "Other Recoveries",
                                        "label": _("Other Recoveries"),
                                        "doctype": "Salary Slip"
                                },
                                {
                                        "type" : "report",
                                        "is_query_report": True,
                                        "name": "Summarized Salary Report",
                                        "label": _("Summarized Salary Report"),
                                        "doctype": "Salary Slip",
                                },
				{
                                        "type" : "report",
                                        "is_query_report": True,
                                        "name": "Alimony Report",
                                        "label":_("Alimony Report"),
                                        "doctype" : "Salary Slip"
                                },
                                {
                                        "type" : "report",
                                        "is_query_report": True,
                                        "name": "House Rent Report",
                                        "label": _("House Rent Report"),
                                        "doctype": "Salary Slip",
                                },
                                 {
                                        "type" : "report",
                                        "is_query_report": True,
                                        "name": "Staff Welfare Scheme",
                                        "label": _("Staff Welfare Scheme"),
                                        "doctype": "Salary Slip"
                                },
                                 {
                                        "type" : "report",
                                        "is_query_report": True,
                                        "name": "Adhoc Recoveries",
                                        "label": _("Adhoc Recoveries"),
                                        "doctype": "Salary Slip"
                                }
			]
		},
	]
