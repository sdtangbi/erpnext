// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Increment"] = {
	"filters": [
		{
			"fieldname": "fiscal_year",
			"label": ("Fiscal Year"),
			"fieldtype": "Link",
			"width": "120",
			"options":"Fiscal Year",
			"width": "100",
			"reqd": 1
         },
		 {
			"fieldname": "increment_and_promotion_cycle",
			"label": ("Increment Cycle"),
			"fieldtype": "Select",
			"width": "120",
			"options":["", "January", "July"],
			"width": "100",
			"reqd": 1
         },
		{
			"fieldname": "uinput",
			"label": ("Status"),
			"fieldtype": "Select",
			"width": "120",
			"options":["All", "Draft", "Submitted"],
			"width": "100",
			"reqd": 1,
			"default": "All"
         },
		{			
			"fieldname":"branch",
			"label": ("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": "100"
		},
		
	]
}
