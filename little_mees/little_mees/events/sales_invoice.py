
import frappe
import json
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import now, format_datetime

@frappe.whitelist(allow_guest=False)
def create_sales_invoice(**args):
	"""
	Decider whether it goes to backendjob or not.
	"""	
	try:		        
		requested_json = frappe.request.data.decode('utf-8').replace('\0', '')
		payload_dict = json.loads(requested_json)
		payload_list_data = payload_dict.get("data")
		little_mees_default_settings_values = frappe.get_doc('Little Mees Settings')
		timeout_que = little_mees_default_settings_values.timeout
		length_char = little_mees_default_settings_values.char_length
		order_length = little_mees_default_settings_values.order_length
		if len(str(payload_list_data))>=25000 and len(payload_list_data)<=order_length:
			if len(str(payload_list_data))<=length_char:
				job_id = format_datetime(now(), "ddmmyyyyhhmmss")
				enqueue(
					method=generate_sales_invoice_and_journal_entries, 
					queue='long', timeout=timeout_que, is_async=True, 
					job_name=job_id, is_from_backend_job=True, 
					payload_dict=payload_dict, process_id=job_id
				)
				return {
						"status":True, 
						"message":"moved into backend job with id {job_id}".format(job_id=job_id)
					}
			else:
				return {"status":False, "error":"number of characters greater than {length_char}"
				.format(length_char=str(length_char))}			
		elif len(payload_list_data)>order_length:
			return {"status":False, "error":"number of orders greater than {order_length}"
			.format(order_length=str(order_length))}
		else:
			payload_dict = {"payload_dict":payload_dict}
			return generate_sales_invoice_and_journal_entries(**payload_dict)		
	except Exception as e:
		return {"status":False, "error":str(e)}
		
def generate_sales_invoice_and_journal_entries(**args):
	"""
	sales invoice and relavent Journal Entries engine
	"""
	processed_system_ids = []
	duplicated_system_ids = []
	not_processed_system_ids = []

	if args.get("is_from_backend_job"):
		is_it_from_enque = True
		job_id = args.get("process_id")
	else:
		is_it_from_enque = False
	
	payload_dict = args.get("payload_dict")
	payload_list_data = payload_dict.get("data")
	for order in payload_list_data:

		try:		
			system_id = order.get("system_id")
			# if duplicate or not system_id then move next order
			if not system_id:
				continue
			elif system_id:
				system_id = system_id.strip()
				if system_id and not system_id.isspace():
					system_id_exist_check = frappe.db.exists({"doctype":"Sales Invoice", 
						"system_id":system_id})
				else:
					continue        					
				if system_id_exist_check:
					duplicated_system_ids.append(system_id)
					continue
			
			customer = order.get("platform_name")
			if customer:
				customer = customer.strip()
				if customer and not customer.isspace():
					customer_exist_check = frappe.db.exists(
						{"doctype":"Customer", "customer_name":customer})
				else:
					customer_exist_check = None    
			else:
				customer_exist_check = None    

			if not customer_exist_check:
				not_processed_system_ids.append({"system_id":system_id, 
				"reason":"Platform {platform_name} does not exist.".format(platform_name=customer)})
				continue

			little_mees_default_settings_values = frappe.get_doc('Little Mees Settings')
			company = little_mees_default_settings_values.company
			cost_center_invoice = little_mees_default_settings_values.cost_center
			currency_default = little_mees_default_settings_values.currency
			exchange_rate_default = little_mees_default_settings_values.exchange_rate
			party_type_supplier = little_mees_default_settings_values.party_type_supplier
			party_type_customer = little_mees_default_settings_values.party_type_customer
			same_platform_check_value = little_mees_default_settings_values.same_platform_check_value

			order_date = order.get("order_date")
			if not order_date:
				not_processed_system_ids.append({"system_id":system_id, 
				"reason":"Order date is required"})
				continue

			from frappe.utils.data import today
			due_date = today()

			item_list = []
			is_item_loop_break = False	
			for item in order.get("order_items"):
				item_code = item.get("item_code")
				if item_code:
					item_code = item_code.strip()
					if item_code and not item_code.isspace():		
						item_exist_check = frappe.db.exists({"doctype":"Item", 
							"description":str(item_code)})
					else:
						item_exist_check = None        
				else:
					item_exist_check = None        
				if not item_exist_check:
					is_item_loop_break = True
					break        	
				item_list.append({
					"item_code":item_exist_check[0][0],
					"qty":item.get("qty"),
					"rate":item.get("rate")
				})
			if is_item_loop_break:
				not_processed_system_ids.append({"system_id":system_id, 
				"reason":"Item {item} does not exist".format(item=item_code)})
				continue			
			
			# calculate the delevery cost		
			if (order.get("delivered_by") == same_platform_check_value):
				
				supplier_exist_check = frappe.db.exists({"doctype":"Supplier", 
					"supplier_name":customer})    
				if not supplier_exist_check:
					not_processed_system_ids.append({"system_id":system_id,
						"reason":"Supplier {supplier_name} does not exist.".format(supplier_name=customer)})
					continue
				vat_amount = round(
					(
						float(order.get("statistics").get("order_commissions").get("delivery_commission")
						)*5.0)/100.0, 2)
				credit_amount_with_vat = round(
					float(
						order.get("statistics").get("order_commissions").get("delivery_commission")
						)+vat_amount,2)

				delivery_commission_cost = {
						"debit": {
							"cost_center": cost_center_invoice,
							"account_currency": currency_default,
							"account": little_mees_default_settings_values.delivery_commission_cost_account_head,
							"exchange_rate": exchange_rate_default,
							"debit": order.get("statistics").get("order_commissions").get("delivery_commission"),
							"credit": 0,
							"debit_in_account_currency": order.get("statistics").get("order_commissions").get("delivery_commission"),
							"credit_in_account_currency": 0
							},
							"debit_2": {
							"cost_center": cost_center_invoice,
							"account_currency": currency_default,
							"account": little_mees_default_settings_values.vat_account_head,
							"exchange_rate": exchange_rate_default,
							"debit": vat_amount,
							"credit": 0,
							"debit_in_account_currency": vat_amount,
							"credit_in_account_currency": 0
							},
							"credit": {
							"party_type": party_type_supplier,
							"party": customer,
							"cost_center": cost_center_invoice,
							"account_currency": currency_default,
							"account": little_mees_default_settings_values.liability_account_head,
							"exchange_rate": exchange_rate_default,
							"debit": 0,
							"credit": credit_amount_with_vat,
							"debit_in_account_currency": 0,
							"credit_in_account_currency": credit_amount_with_vat
							}
				}
			else:
				if order.get("delivered_by"):
					supplier_name = order.get("delivered_by")
					supplier_name = supplier_name.strip()
					if supplier_name and not supplier_name.isspace(): 
						supplier_exist_check = frappe.db.exists({"doctype":"Supplier", 
							"supplier_name":supplier_name})
					else:
						supplier_exist_check = None        
				else:
					supplier_exist_check = None                    
				if not supplier_exist_check:
					not_processed_system_ids.append({"system_id":system_id,"reason":"Supplier {supplier_name} does not exist.".format(supplier_name=order.get("delivered_by"))})
					continue
				vat_amount = round(
					(
						float(
							order.get("statistics").get("order_commissions").get("delivery_charge")
							)*5.0)/100.0,2)	

				credit_amount_with_vat = round(
					float(
						order.get("statistics").get("order_commissions").get("delivery_charge")
						)+vat_amount,2)		

				delivery_charge_cost = {
						"debit": {
							"cost_center": cost_center_invoice,
							"account_currency": currency_default,
							"account": little_mees_default_settings_values.delivery_charge_cost_account_head,
							"exchange_rate": exchange_rate_default,
							"debit": order.get("statistics").get("order_commissions").get("delivery_charge"),
							"credit": 0,
							"debit_in_account_currency": order.get("statistics").get("order_commissions").get("delivery_charge"),
							"credit_in_account_currency": 0
							},
							"debit_2": {
							"cost_center": cost_center_invoice,
							"account_currency": currency_default,
							"account": little_mees_default_settings_values.vat_account_head,
							"exchange_rate": exchange_rate_default,
							"debit": vat_amount,
							"credit": 0,
							"debit_in_account_currency": vat_amount,
							"credit_in_account_currency": 0
							},
							"credit": {
							"party_type": party_type_supplier,
							"party": order.get("delivered_by"),
							"cost_center": cost_center_invoice,
							"account_currency": currency_default,
							"account": little_mees_default_settings_values.liability_account_head,
							"exchange_rate": exchange_rate_default,
							"debit": 0,
							"credit": credit_amount_with_vat,
							"debit_in_account_currency": 0,
							"credit_in_account_currency": credit_amount_with_vat
							}
				}

			# create journel entries for the order			
			journal_entry_system_id_exist_check = frappe.db.exists({"doctype":"Journal Entry", "system_id":system_id})
			if journal_entry_system_id_exist_check:
				journal_entry_doc = frappe.get_doc("Journal Entry", journal_entry_system_id_exist_check[0][0])
			else:
				journal_entry_doc = frappe.new_doc("Journal Entry")
			journal_entry_doc.company = company
			journal_entry_doc.posting_date = order_date
			journal_entry_doc.system_id = system_id
			is_cost_break_down_loop_break = False
			test_dict = {}
			debit_test = 0.0
			credit_test = 0.0
			for each_dict_cost_breakdown in order.get("costs_breakdown"):
				supplier_name = order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("party")
				if supplier_name:
					supplier_name = supplier_name.strip()
					if supplier_name and not supplier_name.isspace():
						supplier_exist_check = frappe.db.exists({"doctype":"Supplier", 
							"supplier_name":supplier_name})
					else:
						supplier_exist_check = None
				else:
					supplier_exist_check = None                    
				if not supplier_exist_check:
					is_cost_break_down_loop_break = True
					break    
				journal_entry_doc.append("accounts", {
					"account":"{0}".format(order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("account")),
					"cost_center":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("cost_center"),
					"account_currency":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("account_currency"),
					"exchange_rate":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("exchange_rate"),
					"debit":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("debit"),
					"credit":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("credit"),
					"debit_in_account_currency":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("debit_in_account_currency"),
					"credit_in_account_currency": order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("credit_in_account_currency")	
				})

				vat_amount = round((
					float(
						order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("debit")
						)*5.0)/100.0,2)
				

				journal_entry_doc.append("accounts", {
					"account":little_mees_default_settings_values.vat_account_head,
					"cost_center":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("cost_center"),
					"account_currency":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("account_currency"),
					"exchange_rate":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("exchange_rate"),
					"debit":vat_amount,
					"credit":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("credit"),
					"debit_in_account_currency":vat_amount,
					"credit_in_account_currency": order.get("costs_breakdown").get(each_dict_cost_breakdown).get("debit").get("credit_in_account_currency")	
				})

				credit_amount_with_vat = round(
					float(
						order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("credit")
						)+vat_amount,2)

				journal_entry_doc.append("accounts", {
					"party_type":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("party_type"),
					"party":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("party"),
					"cost_center":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("cost_center"),
					"account_currency":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("account_currency"),
					"account":little_mees_default_settings_values.liability_account_head,
					"exchange_rate":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("exchange_rate"),
					"debit":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("debit"),
					"credit":credit_amount_with_vat,
					"debit_in_account_currency":order.get("costs_breakdown").get(each_dict_cost_breakdown).get("credit").get("debit_in_account_currency"),
					"credit_in_account_currency": credit_amount_with_vat	
				})
			if is_cost_break_down_loop_break:
				not_processed_system_ids.append({"system_id":system_id, 
				"reason":"Supplier {supplier} does not exist".format(
					supplier=supplier_name)
				})
				continue    
			if order.get("delivered_by") == same_platform_check_value:
				journal_entry_doc.append("accounts", delivery_commission_cost.get("debit"))
				journal_entry_doc.append("accounts", delivery_commission_cost.get("debit_2"))
				journal_entry_doc.append("accounts", delivery_commission_cost.get("credit"))
			else:
				journal_entry_doc.append("accounts", delivery_charge_cost.get("debit"))
				journal_entry_doc.append("accounts", delivery_charge_cost.get("debit_2"))
				journal_entry_doc.append("accounts", delivery_charge_cost.get("credit"))

			sales_invoice_doc = frappe.new_doc("Sales Invoice")
			sales_invoice_doc.update({
				"company":company,
				"customer":customer,
				"order_date":order_date,
				"due_date":due_date,
				"system_id":system_id,
				"discount_amount":float(order.get("discount")),
				"cost_center":cost_center_invoice,
				"apply_discount_on":little_mees_default_settings_values.apply_discount_on
				})

			for item in item_list:
				sales_invoice_doc.append("items", {
					"item_code":item.get("item_code"),
					"qty":item.get("qty"),
					"rate":item.get("rate"),
					"cost_center":cost_center_invoice
				})

			sales_invoice_extra_income = [{
					"account_head":little_mees_default_settings_values.delivery_fee_account_head,
					"charge_type":little_mees_default_settings_values.sales_invoice_charge_type,
					"cost_center":cost_center_invoice,
					"tax_amount":order.get("delivery_fee"),
					"base_tax_amount":order.get("delivery_fee"),
					"description":little_mees_default_settings_values.delivery_fee_discription
				},
				{
					"account_head":little_mees_default_settings_values.vat_account_head,
					"charge_type":little_mees_default_settings_values.incom_vat_charge_type,
					"row_id":1,
					"cost_center":"Main - LM",
					"rate":5.0,
					"description":"VAT 5%"
				}
			]

			for extra_income in sales_invoice_extra_income:
				sales_invoice_doc.append("taxes", extra_income)
				
			sales_invoice_doc.append("sales_invoice_extras", {
				"platform_id":order.get("platform_id"),
				"brand":order.get("brand"),
				"kitchen":order.get("kitchen"),
				"delivery_by":order.get("delivered_by"),
				"order_platform":order.get("order_platform"),
				"emirate_or_state":order.get("state"),
				"payment_method":order.get("payment_method").upper(),
				"total_gross_sale":order.get("total_gross_sale"),
				"delivery_fee":order.get("delivery_fee"),
				"discount":order.get("discount"),
				"net_sale_after_discount":order.get("net_sale_after_discount"),
				"kitchen_food_cost":order.get("costs_breakdown").get("kitchen_cost_without_vat"),
				"packaging":order.get("costs_breakdown").get("packaging_cost_without_vat"),
				"order_taking_commission":order.get("statistics").get("order_commissions").get("order_taking_commission"),
				"delivery_commission":order.get("statistics").get("order_commissions").get("delivery_commission"),
				"credit_card_fees":order.get("statistics").get("order_commissions").get("credit_card_fee_without_vat"),
				"delivery_platform_charges":order.get("delivery_platform_charges")
			})
			# append system_id to processed_system_id
			processed_system_ids.append(system_id)
			sales_invoice_doc.insert()
			sales_invoice_doc.save()
			sales_invoice_doc.submit()

			journal_entry_doc.insert()
			journal_entry_doc.save()
			journal_entry_doc.submit()
		except Exception as e:
			not_processed_system_ids.append({"system_id":system_id, 
				"reason":str(e)
				})
			continue		

	if not is_it_from_enque:
		return {"status":any(processed_system_ids), "processed_system_ids":processed_system_ids, 
			"duplicate_system_ids":duplicated_system_ids, "not_processed_system_ids":not_processed_system_ids}
	else:
		save_response_in_databases(**{
			"job_id":job_id,
			"processed_system_ids":processed_system_ids,
			"duplicated_system_ids":duplicated_system_ids,
			"not_processed_system_ids":not_processed_system_ids
		})


def save_response_in_databases(**args):
	"""
	store background job details
	"""
	job_id = args.get("job_id")
	processed_system_ids = args.get("processed_system_ids")
	duplicate_system_ids = args.get("duplicated_system_ids")
	not_processed_system_ids = args.get("not_processed_system_ids")
	new_backend_job_add = frappe.new_doc("Large Order Process Status")
	new_backend_job_add.job_id = args.get("job_id")
	for processed_system_id in processed_system_ids:
		new_backend_job_add.append("processed_system_ids", {
			"system_ids":processed_system_id
		})

	for duplicate_system_id in duplicate_system_ids:
		new_backend_job_add.append("duplicated_system_ids", {
			"system_ids":duplicate_system_id
		})

	for not_processed_system_id_dict in not_processed_system_ids:
		new_backend_job_add.append("not_processed_system_ids", {
			"system_ids":not_processed_system_id_dict.get("system_id"),
			"reason":not_processed_system_id_dict.get("reason")
		})
	new_backend_job_add.save(ignore_permissions=True)			