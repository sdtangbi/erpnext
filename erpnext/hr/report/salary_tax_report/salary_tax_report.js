// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Tax Report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.defaults.get_user_default("year_start_date"),
		},		
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.defaults.get_user_default("year_end_date"),
		},
		{
			"fieldname":"gross_amt",
			"label": __("Gross Amount"),
			"fieldtype": "Float",
			"default": 0.00
		}
	]
}
