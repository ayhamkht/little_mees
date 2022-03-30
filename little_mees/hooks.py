# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "little_mees"
app_title = "Little Mees"
app_publisher = "Kunhi Mohamed"
app_description = "Connect Little Mees Dashboard To ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "mohamed@craftinteractive.ae"
app_license = "MIT"


fixtures = [
    {
    "dt":
    "Custom Field",
    "filters": [
            [
                "name", "in",
                [
                    # Sales Invoice Date
                    'Sales Invoice-system_id',
                    'Sales Invoice-sales_invoice_extras',
                    'Sales Invoice-order_date',
                    # Journale Entry
                    'Journal Entry-system_id',
                ]
            ]
        ]
    }
]                
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/little_mees/css/little_mees.css"
# app_include_js = "/assets/little_mees/js/little_mees.js"

# include js, css files in header of web template
# web_include_css = "/assets/little_mees/css/little_mees.css"
# web_include_js = "/assets/little_mees/js/little_mees.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "little_mees.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "little_mees.install.before_install"
# after_install = "little_mees.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "little_mees.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
    "Item": {
        "validate": "little_mees.little_mees.events.item.item_description_strip_html"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"little_mees.tasks.all"
# 	],
# 	"daily": [
# 		"little_mees.tasks.daily"
# 	],
# 	"hourly": [
# 		"little_mees.tasks.hourly"
# 	],
# 	"weekly": [
# 		"little_mees.tasks.weekly"
# 	]
# 	"monthly": [
# 		"little_mees.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "little_mees.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "little_mees.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "little_mees.task.get_dashboard_data"
# }

