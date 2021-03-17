frappe.listview_settings['Feedback Setting'] = {
	add_fields: ["title", "status", "start_date", "end_date"],
	get_indicator: function (doc) {
		if (doc.status === "Open") {
			return [__("Open"), "green", "status,=,Open"];
		} else if (doc.status === "Close") {
			return [__("Close"), "orange", "status,=,Close"];
        }
	},
};
