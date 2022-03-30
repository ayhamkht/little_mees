import datetime
import frappe
import json
from frappe.utils.data import strip_html

@frappe.whitelist(allow_guest=False)
def create_items(**args):
    """
    Create items
    """
    try:
        saved_items = []
        duplicated_items = []
        not_processed_items = []
        requested_json = frappe.request.data.decode('utf-8').replace('\0', '')
        payload_dict = json.loads(requested_json)
        payload_list_data = payload_dict.get("items")
        if len(payload_list_data)>6000 or len(str(payload_list_data))>100000:
            return {
                "status":False, 
                "error":"number of items greater than 6000 or string length larger"
                }
        for item in payload_list_data:
            try:
                item = item.strip()
                if item and not item.isspace():
                    item_exist_check = frappe.db.exists({"doctype":"Item", "description":str(item)})
                else:
                    continue    
                if item_exist_check:
                    duplicated_items.append(item)
                    continue
                new_item = frappe.new_doc("Item")
                new_item.update({
                    "description":item,
                    "item_group":"Consumable",
                    "stock_uom":"Nos"
                })
                new_item.insert()
                saved_items.append(item)
            except Exception as e:
                not_processed_items.append({"item":item, 
				"reason":str(e)})
        if saved_items:	
            return {"status":True, "saved_items":saved_items, 
                "duplicated_items":duplicated_items, "not_processed_items":not_processed_items}
        return {"status":False, "saved_items":saved_items, 
            "duplicated_items":duplicated_items, "not_processed_items":not_processed_items}
    except Exception as e:
        return {"status":False, "error":str(e)}

def item_description_strip_html(doc, handler=None):
    """
    strip_html from string
    """
    doc.description = strip_html(doc.description)
    