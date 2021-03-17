// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Performance Evaluation', {
	// refresh: function(frm) {

	// }
	onload: function (frm) {
		apply_filter(frm)
		
	},
	pms_calendar: function (frm) {
	
		get_target(frm);
		get_competency(frm);
		
	},	
});

function apply_filter(frm) {
	cur_frm.set_query('pms_calendar', function () {
		return {
			'filters': {
				'name': frappe.defaults.get_user_default('fiscal_year'),
				'docstatus': 1
			}
		};
	});
}
//get traget from py file
function get_target(frm) {
	
	if (frm.doc.required_to_set_target) {
		frappe.call({
			method: 'get_target',
			doc: frm.doc,
			callback: function () {
				frm.refresh_field('evaluate_target_item');
				frm.refresh_field()
			}
		})
	}
}
//get competency from py file
function get_competency(frm) {
	
	if (frm.doc.employee) {
		frappe.call({
			method: "get_competency",
			doc: frm.doc,
			callback: function () {
				frm.refresh_field('evaluate_competency_item');
				frm.refresh_field()
			}
		})
	}
}
