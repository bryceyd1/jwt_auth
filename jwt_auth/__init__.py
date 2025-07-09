__version__ = "0.0.1"

import frappe

def get_default_company():
	"""Return default company for the app"""
	return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

# Ensure JWT settings are created on startup
def install():
	"""Install the app"""
	# Create default JWT Auth Settings if it doesn't exist
	if not frappe.db.exists("JWT Auth Settings", "JWT Auth Settings"):
		settings = frappe.get_doc({
			"doctype": "JWT Auth Settings",
			"enabled": 0,
			"enable_login": 1,
			"enable_user_reg": 1
		})
		settings.insert(ignore_permissions=True)
		frappe.db.commit()
