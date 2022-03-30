import datetime
import frappe
import json
import requests
import frappe

@frappe.whitelist(allow_guest=False)
def create_suppliers(**args):
    """
    Creates suppliers
    """
    try:
        saved_suppliers = []
        duplicated_suppliers = []
        not_processed_suppliers = []
        requested_json = frappe.request.data.decode('utf-8').replace('\0', '')
        payload_dict = json.loads(requested_json)
        payload_list_data = payload_dict.get("suppliers")
        little_mees_default_settings_values = frappe.get_doc('Little Mees Settings')
        if len(payload_list_data)>2500 or len(str(payload_list_data))>100000:
            return {
                "status":False, 
                "error":"number of items greater than 2500 or string length larger"
                }
        for supplier in payload_list_data:
            try:
                supplier = supplier.strip()
                if supplier and not supplier.isspace():
                    supplier_exist_check = frappe.db.exists({"doctype":"Supplier", "supplier_name":supplier})
                else:
                    continue    
                if supplier_exist_check:
                    duplicated_suppliers.append(supplier)
                    continue
                new_supplier = frappe.new_doc("Supplier")
                new_supplier.update({
                    "supplier_name":supplier,
                    "supplier_type":little_mees_default_settings_values.supplier_type,
                    "supplier_group":little_mees_default_settings_values.supplier_group,
                    "country":little_mees_default_settings_values.supplier_country
                })
                new_supplier.insert()
                saved_suppliers.append(supplier)
            except Exception as e:
                not_processed_suppliers.append({"supplier":supplier, 
                "reason":str(e)})
        if saved_suppliers:	
            return {"status":True, "saved_suppliers":saved_suppliers, 
                "duplicated_suppliers":duplicated_suppliers, "not_processed_suppliers":not_processed_suppliers}
        return {"status":False, "saved_suppliers":saved_suppliers, 
            "duplicated_suppliers":duplicated_suppliers, "not_processed_suppliers":not_processed_suppliers}
    except Exception as e:
        return {"status":False, "error":str(e)}            
                
