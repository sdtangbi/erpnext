// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.cscript.display_activity_log = function(msg) {
	if(!cur_frm.ss_html)
		cur_frm.ss_html = $a(cur_frm.fields_dict['activity_log'].wrapper,'div');
	if(msg) {
		cur_frm.ss_html.innerHTML =
			'<div class="padding"><h4>'+__("Activity Log:")+'</h4>'+msg+'</div>';
	} else {
		cur_frm.ss_html.innerHTML = "";
	}
}

/*/Create Increment
//-----------------------
cur_frm.cscript.create_increment = function(doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");
	var callback = function(r, rt){
		if (r.message)
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', args={'method':'create_increment','docs':doc},callback);
}

//Remove Increment
//-----------------------
cur_frm.cscript.remove_increment = function(doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");
	var callback = function(r, rt){
		if (r.message)
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', args={'method':'remove_increment','docs':doc},callback);
}

//Submit Increment
//-----------------------
cur_frm.cscript.submit_increment = function(doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");

	frappe.confirm(__("Do you really want to Submit all Salary Increment for month {0} and year {1}", [doc.month, doc.fiscal_year]), function() {
		// clear all in locals
		if(locals["Salary Increment"]) {
			$.each(locals["Salary Increment"], function(name, d) {
				frappe.model.remove_from_locals("Salary Increment", name);
			});
		}

		var callback = function(r, rt){
			if (r.message)
				cur_frm.cscript.display_activity_log(r.message);
		}

		return $c('runserverobj', args={'method':'submit_increment','docs':doc},callback);
	});
} */

frappe.ui.form.on('Process Increment', {
	refresh: function(frm) {
		frm.disable_save();
	},
	create_increment: function(frm){
		process_increment(frm, "create");
	},
	
	remove_increment: function(frm) {
        process_increment(frm, "remove");
    },

	submit_increment: function(frm){
		process_increment(frm, "submit");
	},
	// Following code commented by SHIV on 2018/10/16
	/*
	"remove_increment": function(frm) {
		// clear all in locals
		if(locals["Salary Increment"]) {
			$.each(locals["Salary Increment"], function(name, d) {
				frappe.model.remove_from_locals("Salary Increment", name);
			});
		}

		return frappe.call({
			method: "remove_increment",
			doc: frm.doc,
			callback: function(r, rt) {
				frm.refresh_fields();
				if (r.message)
					cur_frm.cscript.display_activity_log(r.message);
			},
			freeze: true,
			freeze_message: "Removing Increments.... Please Wait",
		});
        },

	"create_increment": function(frm) {
		// clear all in locals
		if(locals["Salary Increment"]) {
			$.each(locals["Salary Increment"], function(name, d) {
				frappe.model.remove_from_locals("Salary Increment", name);
			});
		}

		return frappe.call({
			method: "create_increment",
			doc: frm.doc,
			callback: function(r, rt) {
				frm.refresh_fields();
				if (r.message)
					cur_frm.cscript.display_activity_log(r.message);
			},
			freeze: true,
			freeze_message: "Creating Increments.... Please Wait",
		});
        },

	"submit_increment": function(frm) {
                frappe.confirm(__("Do you really want to Submit all Salary Increment for month {0} and year {1}", [frm.doc.month, frm.doc.fiscal_year]), function() {
			// clear all in locals
			if(locals["Salary Increment"]) {
				$.each(locals["Salary Increment"], function(name, d) {
					frappe.model.remove_from_locals("Salary Increment", name);
				});
			}

                        return frappe.call({
                                method: "submit_increment",
                                doc: frm.doc,
                                callback: function(r, rt) {
                                        frm.refresh_fields();
                                        if (r.message)
                                                cur_frm.cscript.display_activity_log(r.message);
                                },
                                freeze: true,
                                freeze_message: "Submitting Increments.... Please Wait",
                        });
                })
    },
	*/
});

//Added by SHIV on 2018/10/15
var process_increment = function(frm, process_type){
	var head_log="", body_log="", msg="", msg_other="";
	cur_frm.cscript.display_activity_log('');
	head_log = '<div class="container"><h4>'+__("Activity Log:")+'</h4><table class="table">';
	frm.set_value("progress", "");
	frm.refresh_field("progress");
	
	if(process_type == "create"){
		msg = "Creating Salary Increment(s).... Please Wait!!!";
		msg_other = "created";
	} else if(process_type == "remove"){
		msg = "Removing Salary Increment(s).... Please Wait!!!";
		msg_other = "removed";
	} else{
		msg = "Submitting Salary Increment(s).... Please Wait!!!";
		msg_other = "submitted";
	}
	
	return frappe.call({
		method: "get_emp_list",
		doc: frm.doc,
		args: {"process_type": process_type},
		callback: function(r, rt){
			if(r.message){
				var counter=0;
				r.message.forEach(function(rec) {
					counter += 1;
					frm.set_value("progress", "Processing "+counter+"/"+r.message.length+" salary increment(s) ["+Math.round((counter/r.message.length)*100)+"% completed]");
					frm.refresh_field("progress");
					frm.refresh_field("activity_log");
					
					cur_frm.call({
						method: "process_increment",
						doc: frm.doc,
						args: {"process_type": process_type, "name": rec.name},
						callback: function(r2, rt2){
							body_log = r2.message+body_log
							cur_frm.ss_html.innerHTML = head_log+body_log
						},
						freeze: true,
					});
				});
			} else {
				body_log = '<div style="color:#fa3635;">No employee for the above selected criteria OR salary increment(s) already '+msg_other+'</div>';
				msgprint(body_log);
				cur_frm.ss_html.innerHTML = head_log+body_log;
			}
		},
		freeze: true,
		freeze_message: msg,
	});
	cur_frm.ss_html.innerHTML += '</table></div>';
}