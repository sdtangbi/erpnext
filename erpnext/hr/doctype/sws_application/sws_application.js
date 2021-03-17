// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "employee_name", "employee_name")

frappe.ui.form.on('SWS Application', {
	refresh: function(frm) {
		if(!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today())
		}
	}
});

cur_frm.fields_dict['items'].grid.get_field('reference_document').get_query = function(frm, cdt, cdn) {
	if (!frm.employee) {
                frm.employee = "dhskhfgskhfgsfhksfsjhbaf"
        }
        return {
                filters: {
                        "parent": frm.employee
                }
        }
}


