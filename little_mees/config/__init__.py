from __future__ import unicode_literals
import frappe
from frappe import _
__version__ = '0.0.1'


from erpnext.config import accounts
data_accounts = accounts.get_data()

#accounts module desktop
def get_data_accounts(data_accounts=data_accounts):
    for row in data_accounts:
        if row['label'] == 'Accounts Payable':
           for rowitem in row['items']:
               if rowitem['name'] == "Accounts Payable":
                   row['items'].remove(rowitem)
    return data_accounts
    
accounts.get_data = get_data_accounts