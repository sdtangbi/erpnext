// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salary Component', {
	onload: function(frm){
		frm.toggle_reqd(["payment_method"], (frm.doc.type == 'Earning' ? 1 : 0));
	},
	refresh: function(frm) {
		frm.toggle_reqd(["payment_method"], (frm.doc.type == 'Earning' ? 1 : 0));
	},
	payment_method: function(frm){
		frm.toggle_reqd(["payment_method"], (frm.doc.type == 'Earning' ? 1 : 0));
	}
});
