// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Target Set Up', {
	employee: function (frm) {
		get_competency(frm)
	},
	get_competency: function (frm) {
		get_competency(frm)
	},
	onload: function (frm) {
		apply_filter(frm)
		filter_supervisor(frm)
	},
	date:function(frm){
		today_date(frm)
	}
});

function filter_supervisor(frm){
	frappe.form.link_formatters['Employee'] = function(value, doc) {
		if(doc.employee_name && doc.employee_name !== value && doc.employee === value) {
			console.log()
			return value + ': ' + doc.employee_name;
		} else {
			return value + ': '+ doc.supervisor_name;
		}
	}
}

function today_date(frm){
	frm.set_value("date",frappe.datetime.get_today())
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
function get_competency(frm) {
	//get competency from py file
	if (frm.doc.designation) {
		return frappe.call({
			method: 'get_competency',
			doc: frm.doc,
			callback: function () {
				frm.refresh_field('competency');
				frm.refresh_field()
			}
		})
	} else {
		frappe.msgprint('Your Designation is not defined under Employee Category')
	}
}