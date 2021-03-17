// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt



frappe.provide("erpnext.hr");

erpnext.hr.SSControlPanel = frappe.ui.form.Controller.extend({
	refresh: function() {
		this.frm.disable_save();
		this.show_upload();
		this.setup_import_progress();
	},

	get_template:function() {
		window.location.href = repl(frappe.request.url +
			'?cmd=%(cmd)s', {
				cmd: "erpnext.hr.doctype.upload_salary_structure.upload_salary_structure.get_template",
			});
	},

	show_upload() {
		var $wrapper = $(cur_frm.fields_dict.upload_html.wrapper).empty();
		new frappe.ui.FileUploader({
			wrapper: $wrapper,
			method: 'erpnext.hr.doctype.upload_salary_structure.upload_salary_structure.upload'
		});
	},

	setup_import_progress() {
		var $log_wrapper = $(this.frm.fields_dict.import_log.wrapper).empty();

		frappe.realtime.on('import_ss', (data) => {
			if (data.progress) {
				this.frm.dashboard.show_progress('Import Salary Structure', data.progress / data.total * 100,
					__('Importing {0} of {1}', [data.progress, data.total]));
				if (data.progress === data.total) {
					this.frm.dashboard.hide_progress('Import Salary Structure');
				}
			} else if (data.error) {
				this.frm.dashboard.hide();
				let messages = [`<th>${__('Error in some rows')}</th>`].concat(data.messages
					.filter(message => message.includes('Error'))
					.map(message => `<tr><td>${message}</td></tr>`))
					.join('');
				$log_wrapper.append('<table class="table table-bordered">' + messages);
			} else if (data.messages) {
				this.frm.dashboard.hide();
				let messages = [`<th>${__('Import Successful')}</th>`].concat(data.messages
					.map(message => `<tr><td>${message}</td></tr>`))
					.join('');
				$log_wrapper.append('<table class="table table-bordered">' + messages);
			}
		});
	},

	show_upload_old: function() {
		var me = this;
		var $wrapper = $(cur_frm.fields_dict.upload_html.wrapper).empty();
		// upload
		frappe.upload.make({
			parent: $wrapper,
			args: {
				method: 'erpnext.hr.doctype.upload_salary_structure.upload_salary_structure.upload'
			},
			sample_url: "e.g. http://xx.com/somefile.csv",
			callback: function(attachment, r) {
				var $log_wrapper = $(cur_frm.fields_dict.import_log.wrapper).empty();

				if(!r.messages) r.messages = [];
				// replace links if error has occured
				if(r.exc || r.error) {
					r.messages = $.map(r.message.messages, function(v) {
						var msg = v.replace("Inserted", "Valid")
							.replace("Updated", "Valid").split("<");
						if (msg.length > 1) {
							v = msg[0] + (msg[1].split(">").slice(-1)[0]);
						} else {
							v = msg[0];
						}
						return v;
					});

					r.messages = ["<h4 style='color:red'>"+__("Import Failed!")+"</h4>"]
						.concat(r.messages)
				} else {
					r.messages = ["<h4 style='color:green'>"+__("Import Successful!")+"</h4>"].
						concat(r.message.messages)
				}

				$.each(r.messages, function(i, v) {
					var $p = $('<p>').html(v).appendTo($log_wrapper);
					if(v.substr(0,5)=='Error') {
						$p.css('color', 'red');
					} else if(v.substr(0,8)=='Inserted') {
						$p.css('color', 'green');
					} else if(v.substr(0,7)=='Updated') {
						$p.css('color', 'green');
					} else if(v.substr(0,5)=='Valid') {
						$p.css('color', '#777');
					}
				});
			}
		});

		// rename button
		$wrapper.find('form input[type="submit"]')
			.attr('value', 'Upload and Import')
	}
})

cur_frm.cscript = new erpnext.hr.SSControlPanel({frm: cur_frm});
