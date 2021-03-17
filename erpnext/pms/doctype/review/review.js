// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Review', {
	onload: function (frm) {
		apply_filter(frm)
		filter_supervisor(frm)
	},
	pms_calendar: function (frm) {
		get_target(frm);
		get_competency(frm);
	}
});

function filter_supervisor(frm){
	frappe.form.link_formatters['Employee'] = function(value, doc) {
		if(doc.employee_name && doc.employee_name !== value && doc.employee === value) {
			return value + ': ' + doc.employee_name;
		} else {
			return value + ': '+ doc.supervisor_name;
		}
	}
}

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
	if (frm.doc.required_to_set_target && frm.doc.employee) {
		frappe.call({
			method: 'get_target',
			doc: frm.doc,
			callback: function () {
				frm.refresh_field('review_target_item');
				frm.refresh_field()
			}
		})
	}
}

function get_competency(frm) {
	if (frm.doc.employee) {
		frappe.call({
			method: "get_competency",
			doc: frm.doc,
			callback: function () {
				frm.refresh_field('review_competency_item');
				frm.refresh_field()
			}
		})
	}
}
