// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch("employee", "user_id", "user_id")

frappe.ui.form.on('Approver Settings', {
	refresh: function(frm) {
	    cur_frm.set_query("cost_center", function() {
		return {
		    "filters": {
			"is_disabled": 0,
			"is_group": 1,
			"is_company": 0
		    }
		};
	   })
	}
});
