import datetime
import frappe
import json
import requests
import frappe
from frappe.utils.background_jobs import get_jobs

@frappe.whitelist(allow_guest=False)
def back_end_jobs_status(**args):
	"""
	Know the backendjobs status
	"""
	try:
		requested_json = frappe.request.data.decode('utf-8').replace('\0', '')
		payload_dict = json.loads(requested_json)
		payload_list_data = payload_dict.get("job_ids")
		if payload_list_data and len(payload_list_data)>1:
			 return {"status":False, "error":"number of job_ids should be one"}
		else:	 
			little_mees_default_settings_values = frappe.get_doc('Little Mees Settings')
			queued_jobs = get_jobs(site=little_mees_default_settings_values.site_name, 
			key=payload_list_data[0])[little_mees_default_settings_values.site_name]

			the_required_data = frappe.db.sql("""
				select 
						tpsi.system_ids as processed_system_ids, 
						tdsi.system_ids as duplicate_system_ids
					from 
						`tabLarge Order Process Status` tlops
					left join 
						`tabDuplicated System IDs` tdsi 
					on 
						tdsi.parent=tlops.name
					left join 
						`tabProcessed System IDs` tpsi 
					on 
						tpsi.parent=tlops.name
					where 
						tlops.job_id = "{job_id}"    
				;""".format(job_id = payload_list_data[0]), as_dict=True)

			processed_system_ids = []
			duplicated_system_ids = []

			for each_dict in the_required_data:
				if each_dict.get("processed_system_ids") not in processed_system_ids:
					processed_system_ids.append(each_dict.get("processed_system_ids"))
				if each_dict.get("duplicate_system_ids") not in duplicated_system_ids:
					duplicated_system_ids.append(each_dict.get("duplicate_system_ids"))

			the_required_data = {"processed_system_ids":processed_system_ids, 
			"duplicated_system_ids":duplicated_system_ids}

			the_not_processed_data = frappe.db.sql("""
				select  
						tnpsi.system_ids, 
						tnpsi.reason
					from 
						`tabLarge Order Process Status` tlops
					left join 
						`tabNot Processed System IDs` tnpsi 
					on 
						tnpsi.parent=tlops.name
					where 
						tlops.job_id = "{job_id}"    
				;""".format(job_id = payload_list_data[0]), as_dict=True)

			the_required_data["not_processed_system_ids"] = the_not_processed_data

			return {"queued_jobs":queued_jobs, "the_required_data":the_required_data}
	except Exception as e:
		return {"status":False, "error":str(e)} 		    