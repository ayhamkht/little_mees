import datetime
import frappe
import json
import requests
import frappe

@frappe.whitelist(allow_guest=False)
def create_platforms(**args):
	"""
	Creates platforms means create customers
	"""
	try:
		saved_platforms = []
		duplicated_platforms = []
		not_processed_customers = []
		requested_json = frappe.request.data.decode('utf-8').replace('\0', '')
		payload_dict = json.loads(requested_json)
		payload_list_data = payload_dict.get("platforms")
		little_mees_default_settings_values = frappe.get_doc('Little Mees Settings')
		if len(payload_list_data)>2500 or len(str(payload_list_data))>100000:
			return {
				"status":False, 
				"error":"number of items greater than 2500 or string length larger"
				}
		
		for platform in payload_list_data:
			try:
				platform = platform.strip()
				if platform and not platform.isspace():
					platform_exist_check = frappe.db.exists({"doctype":"Customer", "customer_name":platform})
				else:
					continue	
				if platform_exist_check:
					duplicated_platforms.append(platform)
					continue
				new_platform = frappe.new_doc("Customer")
				new_platform.update({
					"customer_name":platform,
					"customer_type":little_mees_default_settings_values.customer_type,
					"customer_group":little_mees_default_settings_values.customer_group,
					"territory":little_mees_default_settings_values.customer_territory
				})
				new_platform.insert()
				saved_platforms.append(platform)
			except Exception as e:
				not_processed_customers.append({"customer":platform, \
				"reason":str(e)})
		if saved_platforms:	
			return {"status":True, "saved_platforms":saved_platforms, 
			"duplicated_platforms":duplicated_platforms, "not_processed_platforms":not_processed_customers}
		return {"status":False, "saved_platforms":saved_platforms, 
			"duplicated_platforms":duplicated_platforms, "not_processed_platforms":not_processed_customers}
	except Exception as e:
		return {"status":False, "error":str(e)} 	