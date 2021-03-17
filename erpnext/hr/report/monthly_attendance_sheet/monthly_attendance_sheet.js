// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt


frappe.query_reports["Monthly Attendance Sheet"] = {
	"filters": [
		{
			"fieldname":"month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": "Jan\nFeb\nMar\nApr\nMay\nJun\nJul\nAug\nSep\nOct\nNov\nDec",
			"default": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
				"Dec"][frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth()],
		},
		/*{
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Select",
			"reqd": 1
		},*/
		{
			"fieldname":"year",
			"label": __("Start Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		}
	],

	"onload": function(me) {
		/*
		return  frappe.call({
			method: "erpnext.hr.report.monthly_attendance_sheet.monthly_attendance_sheet.get_attendance_years",
			callback: function(r) {
				var year_filter = me.filters_by_name.year;
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			}
		});
		*/
	},
	//"formatter":function (row, cell, value, columnDef, dataContext, default_formatter) {
	"formatter":function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		//value = default_formatter(row, cell, value, columnDef, dataContext);
		if (value == "X") {
			//var $value = $(value).css({"background-color": "rgb(208, 73, 73)", "font-weight": "bold"});
			//value = $value.wrap("<p></p>").parent().html();
			value = "<div style='color: rgb(208, 73, 73); background-color: rgb(208, 73, 73); width: 100%; height: 100%; border: -5;'>" + value + "</div>"
		}
		return value;
	}
}
