// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "user_id", "user_id");
cur_frm.add_fetch("employee", "employment_type", "employment_type");
cur_frm.add_fetch("employee", "employee_group", "employee_group");
cur_frm.add_fetch("employee", "grade", "grade");
cur_frm.add_fetch("employee", "branch", "branch");
cur_frm.add_fetch("employee", "cost_center", "cost_center");
cur_frm.add_fetch("employee", "business_activity", "business_activity");

frappe.ui.form.on('Salary Advance', {
	onload: function(frm){
		frm.set_query("employee", function() {
			return {
					"filters": {"status": "Active"}
			}
		});
	},
	
	refresh: function(frm){
		// Following line commented by SHIV on 2020/09/22
		//enable_disable(frm);
	},
			
	total_claim: function(frm){
		cur_frm.set_value("monthly_deduction", Math.ceil(parseFloat(frm.doc.total_claim)/ frm.doc.deduction_month));
	},
	
	deduction_month: function(frm){
		cur_frm.set_value("monthly_deduction", Math.ceil(parseFloat(frm.doc.total_claim)/ frm.doc.deduction_month));
	},
		
	employee: function(frm) {
		get_basic_salary(frm.doc);
	},
});

var get_basic_salary=function(doc){
	cur_frm.call({
		method: "get_basic_salary",
		doc:doc
	});

}

function toggle_form_fields(frm, fields, flag){
	fields.forEach(function(field_name){
		frm.set_df_property(field_name, "read_only", flag);
	});
	
	if(flag){
		frm.disable_save();
	} else {
		frm.enable_save();
	}
}

function enable_disable(frm){
	var toggle_fields = [];
	var meta = frappe.get_meta(frm.doctype);

	for(var i=0; i<meta.fields.length; i++){
		if(meta.fields[i].hidden === 0 && meta.fields[i].read_only === 0 && meta.fields[i].allow_on_submit === 0){
			toggle_fields.push(meta.fields[i].fieldname);
		}
	}
	
	toggle_form_fields(frm, toggle_fields, 1);
	
	if(frm.doc.__islocal){
		toggle_form_fields(frm, toggle_fields, 0);
	}
	else {
		// Employee
		if(in_list(frappe.user_roles, "Employee") && (frm.doc.workflow_state.indexOf("Draft") >= 0 || frm.doc.workflow_state.indexOf("Rejected") >= 0)){
			if(frappe.session.user === frm.doc.owner){
				toggle_form_fields(frm, toggle_fields, 0);
			}
		}
		
		// Approver
		if(in_list(frappe.user_roles, "Approver") && frm.doc.workflow_state.indexOf("Waiting Approval") >= 0){
			if(frappe.session.user === frm.doc.advance_approver){
				toggle_form_fields(frm, toggle_fields, 0);
			}			
		}
		
		if(frm.doc.workflow_state.indexOf("Draft") >= 0 || frm.doc.workflow_state.indexOf("Rejected") >= 0){
			frm.set_df_property("advance_approver", "hidden", 1);
			frm.set_df_property("advance_approver_name", "hidden", 1);
			frm.set_df_property("advance_approver_designation", "hidden", 1);
		}
	}
}

frappe.ui.form.on("Salary Advance", "after_save", function(frm, cdt, cdn){
	if(in_list(frappe.user_roles, "Approver")){
		if (frm.doc.workflow_state && (frm.doc.workflow_state.indexOf("Rejected") >= 0 || frm.doc.workflow_state.indexOf("Rejected by Supervisor") >= 0)){
			frappe.prompt([
				{
					fieldtype: 'Small Text',
					reqd: true,
					fieldname: 'reason'
				}],
				function(args){
					validated = true;
					frappe.call({
						method: 'frappe.core.doctype.communication.email.make',
						args: {
							doctype: frm.doctype,
							name: frm.docname,
							subject: format(__('Reason for {0}'), [frm.doc.workflow_state]),
							content: args.reason,
							send_mail: false,
							send_me_a_copy: false,
							communication_medium: 'Other',
							sent_or_received: 'Sent'
						},
						callback: function(res){
							if (res && !res.exc){
								frappe.call({
									method: 'frappe.client.set_value',
									args: {
										doctype: frm.doctype,
										name: frm.docname,
										fieldname: 'rejection_reason',
										value: frm.doc.rejection_reason ?
											[frm.doc.rejection_reason, '['+String(frappe.session.user)+' '+String(frappe.datetime.nowdate())+']'+' : '+String(args.reason)].join('\n') : frm.doc.workflow_state
									},
									callback: function(res){
										if (res && !res.exc){
											frm.reload_doc();
										}
									}
								});
							}
						}
					});
				},
				//__('Reason for ') + __(frm.doc.workflow_state),
				__('Reason for Rejection'),
				__('Save')
			)
		}
	}
});
