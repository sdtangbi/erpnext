// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Feedback', {
	refresh: function(frm){
		var grid_row = cur_frm.open_grid_row();
		grid_row.insert(true, true);
	},
	onload:function(frm) {
		frm.set_query("feedback_setting", function() {
			return {
				filters: {
					"status":"Open"
				}
			}
		});
	},	
	"recipient": function(frm){
		if(frm.doc.recipient){
			frappe.model.get_value("Employee", {"name":frm.doc.recipient}, ["employee_name", "designation", "department", "branch"],
				function(d){
					frm.set_value("recipient_name", d.employee_name);
					frm.set_value("designation", d.designation);
					frm.set_value("department", d.department);
					frm.set_value("branch", d.branch);
			});
		}
	},
});

cur_frm.fields_dict['item'].grid.get_field('detail_code').get_query = function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	return {
			filters: {'competency_code': d.competency_code}
	}
}


