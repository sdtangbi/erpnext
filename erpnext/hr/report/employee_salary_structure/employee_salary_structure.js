// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Salary Structure"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
                        "fieldname":"branch",
                        "label": __("Branch"),
                        "fieldtype": "Link",
                        "options": "Branch",
                },
                {
                        "fieldname":"employee",
                        "label": __("Employee"),
                        "fieldtype": "Link",
                        "options": "Employee",
			"get_query": function() {
				var branch = frappe.query_report.filters_by_name.branch.get_value();
				if(branch) {
					return {"doctype": "Employee", "filters": {"branch": branch, "status": "Active"}}
				}
				else {
					return {"doctype": "Employee", "filters": {"status": "Active"}}
				}
			}
                },
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "All\nActive\nInactive",
			"default": "Active"
		},
		{
			"fieldname": "grade",
			"label": __("Grade"),
			"fieldtype": "Link",
			"options": "Employee Grade"
		}
	]
}
