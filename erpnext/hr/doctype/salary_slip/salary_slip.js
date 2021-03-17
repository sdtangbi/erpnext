// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
/*
--------------------------------------------------------------------------------------------------------------------------
Version          Author          CreatedOn          ModifiedOn          Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
1.0		  		 SSK		                        26/08/2016         Auto calculations when amount in child changed
1.0				 SSK								30/08/2016		   Modified Auto-calculations
1.0              SSK                                12/09/2016         Modified Auto-calculations
--------------------------------------------------------------------------------------------------------------------------                                                                          
*/

cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('time_sheet', 'total_hours', 'working_hours');

frappe.ui.form.on("Salary Slip", {
	setup: function(frm) {
		frm.get_field('items').grid.editable_fields = [
			{fieldname: 'salary_structure', columns: 2},
			{fieldname: 'from_date', columns: 2},
			{fieldname: 'to_date', columns: 2},
			{fieldname: 'working_days', columns: 1},
			{fieldname: 'leave_without_pay', columns: 1},
			{fieldname: 'payment_days', columns: 1},
		];
		
		frm.fields_dict["timesheets"].grid.get_field("time_sheet").get_query = function(){
			return {
				filters: {
					employee: frm.doc.employee
				}
			}
		}
	},

	onload: function(frm){
		if((cint(frm.doc.__islocal) == 1) && !frm.doc.amended_from){
			if(!frm.doc.month) {
				var today=new Date();
				var month = (today.getMonth()).toString();
				if(month.length>1) frm.doc.month = month;
				else frm.doc.month = '0'+month;
			}
			if(!frm.doc.fiscal_year) frm.doc.fiscal_year = sys_defaults['fiscal_year'];
			refresh_many(['month', 'fiscal_year']);
		}
	},
	
	refresh: function(frm) {
		frm.trigger("toggle_fields");
		/*																													//Commented by SHIV on 2018/09/18
		frm.fields_dict['earnings'].grid.set_column_disp("default_amount", false);
		frm.fields_dict['deductions'].grid.set_column_disp("default_amount", false);
		frm.fields_dict['earnings'].grid.set_column_disp("section_break_5", false);
		frm.fields_dict['deductions'].grid.set_column_disp("section_break_5", false);
		*/
	},
	
	employee: function(frm){
		calculate_others(frm.doc);
	},
	
	company: function(frm) {
		var company = locals[':Company'][frm.doc.company];
		if(!frm.doc.letter_head && company.default_letter_head) {
			frm.set_value('letter_head', company.default_letter_head);
		}
	},

	salary_slip_based_on_timesheet: function(frm) {
		frm.trigger("toggle_fields")
	},

	fiscal_year: function(frm){
		calculate_others(frm.doc);
	},
	
	month: function(frm){
		calculate_others(frm.doc);
	},
	
	arrear_amount: function(frm, cdt, cdn){
		calculate_others(frm.doc);
	},
	
	leave_encashment_amount: function(frm, cdt, cdn){
		calculate_others(frm.doc);
	},
	
	toggle_fields: function(frm) {
		frm.toggle_display(['start_date', 'end_date', 'hourly_wages', 'timesheets'],
			cint(frm.doc.salary_slip_based_on_timesheet)==1);
		/* 																											//Commented by SHIV on 2018/09/18
		frm.toggle_display(['fiscal_year', 'month', 'total_days_in_month', 'leave_without_pay', 'payment_days'],
			cint(frm.doc.salary_slip_based_on_timesheet)==0);
		*/
	}
})

frappe.ui.form.on('Salary Detail', {
	amount: function(frm, cdt, cdn){
		calculate_others(frm.doc);
	},
	
	depends_on_lwp: function(frm, cdt, cdn){
		calculate_others(frm.doc);
	},
	
	earnings_remove: function(doc,dt,dn) {
		calculate_others(cur_frm.doc);		
	}, 
	
	deductions_remove: function(doc,dt,dn) {
		calculate_others(cur_frm.doc);
	}
})

frappe.ui.form.on("Salary Slip Timesheet", {
	time_sheet: function(frm, cdt, cdn) {
		doc = frm.doc;
		cur_frm.cscript.fiscal_year(doc, cdt, cdn)
	}
})

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
	return{
		query: "erpnext.controllers.queries.employee_query"
	}
}

// Added by SHIV on 2018/09/18
var calculate_others = function(doc){
	if (doc.employee){
		cur_frm.call({
			method: "get_emp_and_leave_details",
			doc: doc
		});
	}
}