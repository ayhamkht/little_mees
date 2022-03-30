from __future__ import unicode_literals
from frappe import _
import frappe


def get_data():
    return [
        {
            "label": _("Accounts Payable"),
            "icon": "fa fa-wrench",
			"items": [                
                {
					"type": "report",
					"name": "Accounts Payable",
					"is_query_report": True,
                    "hidden": True
				}
            ]
        }
    ]        


  