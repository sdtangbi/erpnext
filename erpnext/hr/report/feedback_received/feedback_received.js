// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Feedback Received"] = {
	"filters": [
		{
			"fieldname": "corporate_ds",
			"label": "Select",
			"fieldtype": "Select",
			"options":["Feedback_Received", "3Ds", "Competency", "Indicators"],
			"reqd":1
		},
		{
			"fieldname": "fiscal_year",
			"label": "Year",
			"fieldtype": "Link",
			"options": "Fiscal Year"
		},
		{	
			"fieldname": "recipient",
			"label": ("Employee Name"),
			"fieldtype": "Link",
			"options":"Employee",
			"width": "80"
		}
	]
};
