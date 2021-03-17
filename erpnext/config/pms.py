from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("PMS"),
			"items": [
				{
					"type": "doctype",
					"name": "PMS Calendar",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Target Set Up",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Work Competency",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Employee Category",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Review",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Performance Evaluation",
					"onboard": 1
				}
			]
		}	
    ]
