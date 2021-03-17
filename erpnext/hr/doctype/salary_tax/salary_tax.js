// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salary Tax', {
	setup: function(frm) {
		frm.get_docfield("salary_tax_slab").allow_bulk_edit = 1;
	},
	refresh: function(frm) {

	}
});
