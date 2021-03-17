// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
/*
---------------------------------------------------------------------------------------------------------------------------
Version          Author            CreatedOn          ModifiedOn          Remarks
------------ ---------------  ------------------ -------------------  -----------------------------------------------------
2.0		          SHIV		      27/02/2018         					Dynamic get_query added for Salary_Components under
																			tables `earnings` and `deductions`
2.0#CDCL#886	  SHIV 		      06/09/2018 		   					Moved retirement_age, health_contribution, employee_pf, 
																			employer_pf from "HR Settings" to "Employee Group"
---------------------------------------------------------------------------------------------------------------------------
*/

cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('company', 'default_letter_head', 'letter_head');

frappe.ui.form.on('Salary Structure', {
	onload: function(frm, cdt, cdn){
		// Following function is created as a replacement for the following commented block by SHIV on 2020/09/23
		make_ed_table(frm);
		/*
		e_tbl = frm.doc.earnings || [];
		d_tbl = frm.doc.deductions || [];
		
		if (e_tbl.length == 0 && d_tbl.length == 0){
			cur_frm.call({
				method: "make_earn_ded_table",
				doc: frm.doc
			});
		}
		*/
	},
	refresh: function(frm, cdt, cdn) {
		// Following code is commented by SHIV on 2020/09/23
		/*
		frm.trigger("toggle_fields")
		frm.fields_dict['earnings'].grid.set_column_disp("default_amount", false);
		frm.fields_dict['deductions'].grid.set_column_disp("default_amount", false);
		frm.fields_dict['earnings'].grid.set_column_disp("sb_additional_info", false);
		*/		
		// Commented till here by SHIV on 2020/09/23

		/*
		if((!frm.doc.__islocal) && (frm.doc.is_active == 'Yes') && cint(frm.doc.salary_slip_based_on_timesheet == 0)){
			cur_frm.add_custom_button(__('Salary Slip'),
				cur_frm.cscript['Make Salary Slip'], __("Make"));
			cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
		}
		*/
	},
	employee: function(frm, cdt, cdn){
		if (frm.doc.employee) {
			cur_frm.call({
				method: "get_employee_details",
				doc: frm.doc
			});
		}
		calculate_others(frm);
	},
	salary_slip_based_on_timesheet: function(frm) {
		frm.trigger("toggle_fields")
	},
	toggle_fields: function(frm) {
		frm.toggle_display(['salary_component', 'hour_rate'], frm.doc.salary_slip_based_on_timesheet);
		frm.toggle_reqd(['salary_component', 'hour_rate'], frm.doc.salary_slip_based_on_timesheet);
	},
	eligible_for_corporate_allowance: function(frm){
		calculate_others(frm);
	},
	eligible_for_contract_allowance: function(frm){
		calculate_others(frm);
	},
	eligible_for_communication_allowance: function(frm){
		calculate_others(frm);
	},
	eligible_for_fuel_allowances: function(frm){
		calculate_others(frm);
	},
	eligible_for_underground: function(frm){
		calculate_others(frm);
	},
	eligible_for_shift: function(frm){
		calculate_others(frm);
	},
	eligible_for_difficulty: function(frm){
		calculate_others(frm);
	},
	eligible_for_high_altitude: function(frm){
		calculate_others(frm);
	},
	eligible_for_psa: function(frm){
		calculate_others(frm);
	},
	eligible_for_pda: function(frm){
		calculate_others(frm);
	},
	eligible_for_deputation: function(frm){
		calculate_others(frm);
	},
	eligible_for_officiating_allowance: function(frm){
		calculate_others(frm);
	},
	eligible_for_temporary_transfer_allowance: function(frm){
		calculate_others(frm);
	},
	eligible_for_scarcity: function(frm){
		calculate_others(frm);
	},
	eligible_for_cash_handling: function(frm){
		calculate_others(frm);
	},
	eligible_for_honorarium: function(frm){
		calculate_others(frm);
	},
	eligible_for_mpi: function(frm){
		calculate_others(frm);
	},
	eligible_for_sws: function(frm){
		calculate_others(frm);
	},
	eligible_for_gis: function(frm){
		calculate_others(frm);
	},
	eligible_for_pf: function(frm){
		calculate_others(frm);
	},
	eligible_for_health_contribution: function(frm){
		calculate_others(frm);
	},
	ca: function(frm){
		calculate_others(frm);
	},
	contract_allowance: function(frm){
		calculate_others(frm);
	},
	communication_allowance: function(frm){
		calculate_others(frm);
	},
	psa: function(frm){
		calculate_others(frm);
	},
	mpi: function(frm){
		calculate_others(frm);
	},
	officiating_allowance: function(frm){
		calculate_others(frm);
	},
	temporary_transfer_allowance: function(frm){
		calculate_others(frm);
	},
	/*
	lumpsum_temp_transfer_amount: function(frm) {
		calculate_others(frm);
		calculate_totals(frm.doc);
	},
	*/
	fuel_allowances: function(frm){
		calculate_others(frm);
	},
	pda: function(frm){
		calculate_others(frm);
	},
	shift: function(frm){
		calculate_others(frm);
	},
	deputation: function(frm){
		calculate_others(frm);
	},
	underground: function(frm){
		calculate_others(frm);
	},
	difficulty: function(frm){
		calculate_others(frm);
	},
	high_altitude: function(frm){
		calculate_others(frm);
	},
	scarcity: function(frm){
		calculate_others(frm);
	},
	cash_handling: function(frm){
		calculate_others(frm);
	},
	honorarium: function(frm){
		calculate_others(frm);
	},
	// Payment Methods
	ca_method: function(frm){
		calculate_others(frm);
	},
	contract_allowance_method: function(frm){
		calculate_others(frm);
	},
	communication_allowance_method: function(frm){
		calculate_others(frm);
	},
	psa_method: function(frm){
		calculate_others(frm);
	},
	mpi_method: function(frm){
		calculate_others(frm);
	},
	officiating_allowance_method: function(frm){
		calculate_others(frm);
	},
	temporary_transfer_allowance_method: function(frm){
		calculate_others(frm);
	},
	fuel_allowances_method: function(frm){
		calculate_others(frm);
	},
	pda_method: function(frm){
		calculate_others(frm);
	},
	shift_method: function(frm){
		calculate_others(frm);
	},
	deputation_method: function(frm){
		calculate_others(frm);
	},
	underground_method: function(frm){
		calculate_others(frm);
	},
	difficulty_method: function(frm){
		calculate_others(frm);
	},
	high_altitude_method: function(frm){
		calculate_others(frm);
	},
	scarcity_method: function(frm){
		calculate_others(frm);
	},
	cash_handling_method: function(frm){
		calculate_others(frm);
	},
	honorarium_method: function(frm){
		calculate_others(frm);
	}
})

var make_ed_table = function(frm){
	var e_tbl = frm.doc.earnings || [];
	var d_tbl = frm.doc.deductions || [];
	
	if (e_tbl.length == 0 && d_tbl.length == 0){
		cur_frm.call({
			method: "make_earn_ded_table",
			doc: frm.doc
		});
	}
}

frappe.ui.form.on('Salary Detail', {
	amount: function(frm, cdt, cdn) {
		calculate_others(frm);
	},
	
	earnings_remove: function(frm) {
		calculate_others(frm);
	}, 
	
	deductions_remove: function(frm) {
		calculate_others(frm);
	},
	
	total_deductible_amount: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "total_outstanding_amount", parseFloat(d.total_deductible_amount || 0.0)-parseFloat(d.total_deducted_amount || 0.0));
	},
})

var calculate_others = function(frm){
	cur_frm.call({
		method: "update_salary_structure",
		doc: frm.doc,
		callback: function(r, rt) {
			frm.refresh_fields();
		},
		freeze: true,
		freeze_message: "Recalculating..."
	});
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
			return{ query: "erpnext.controllers.queries.employee_query" }
}

cur_frm.cscript['Make Salary Slip'] = function() {
	frappe.model.open_mapped_doc({
		method: "erpnext.hr.hr_custom_functions.make_salary_slip",
		frm: cur_frm
	});
}

// ++++++++++++++++++++ Ver 2.0 BEGINS ++++++++++++++++++++
// Following code added by SHIV on 2018/02/27
frappe.ui.form.on("Salary Structure", "refresh", function(frm) {
    frm.fields_dict['earnings'].grid.get_field('salary_component').get_query = function(doc, cdt, cdn) {
        var doc = locals[cdt][cdn];
        return {
            "query": "erpnext.hr.doctype.salary_structure.salary_structure.salary_component_query",
            filters: {'parentfield': 'earnings'}
        }
    };
});

frappe.ui.form.on("Salary Structure", "refresh", function(frm) {
    frm.fields_dict['deductions'].grid.get_field('salary_component').get_query = function(doc, cdt, cdn) {
        doc = locals[cdt][cdn]
        return {
            "query": "erpnext.hr.doctype.salary_structure.salary_structure.salary_component_query",
            filters: {'parentfield': 'deductions'}
        }
    };
});
// +++++++++++++++++++++ Ver 2.0 ENDS +++++++++++++++++++++
