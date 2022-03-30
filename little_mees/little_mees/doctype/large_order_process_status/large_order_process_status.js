// Copyright (c) 2021, Kunhi Mohamed and contributors
// For license information, please see license.txt
// here is the initial commit..

frappe.ui.form.on('Large Order Process Status', {
	refresh: function(frm) {
		frm.set_df_property("processed_system_ids", "read_only", 1);
		frm.set_df_property("duplicated_system_ids", "read_only", 1);
		frm.set_df_property("not_processed_system_ids", "read_only", 1);
	}
});
