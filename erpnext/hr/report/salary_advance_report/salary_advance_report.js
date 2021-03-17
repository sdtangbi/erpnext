// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Advance Report"] = {
	"filters": [
		{
                        "fieldname": "from_date",
                        "label": __("From Date"),
                        "fieldtype": "Date",
                        "default": frappe.defaults.get_user_default("year_start_date"),
                        "reqd": 1,
                },
                {
                        "fieldname": "to_date",
                        "label": __("To Date"),
                        "fieldtype": "Date",
                        "default": frappe.defaults.get_user_default("year_end_date"),
                        "reqd": 1,
                },
		{
                        "fieldname": "branch",
                        "label": ("Branch"),
                        "fieldtype": "Link",
                        "options": "Branch",
                        "get_query": function() {
                                return {"doctype": "Branch", "filters": {"is_disabled": 0}}
                        }
                },
		{
			"fieldname": "employee",
			"label": ("Employee"),
			"fieldtype" : "Link",
			"options": "Employee",
			"get_query": function() {
                                var branch = frappe.query_report.filters_by_name.branch.get_value();
				if(branch)
					return {"doctype": "Employee", "filters": {"branch": branch }} 
			}
		},
	]
}
