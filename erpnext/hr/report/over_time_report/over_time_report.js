// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Over Time Report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": ("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd" : 1
		},
		{
			"fieldname":"to_date",
			"label": ("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd" : 1			
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
		},
		{
			"fieldname": "grade",
			"label": __("Employee Grade"),
			"fieldtype": "Link",
			"options": "Employee Grade",
		},
		{
			"fieldname": "designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation",
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
	]
}
