import frappe

def after_install():
	"""After installation setup for JWT Auth app"""
	create_jwt_auth_settings()
	frappe.db.commit()

def create_jwt_auth_settings():
	"""Create default JWT Auth Settings document if it doesn't exist"""
	if not frappe.db.exists("JWT Auth Settings", "JWT Auth Settings"):
		try:
			settings = frappe.get_doc({
				"doctype": "JWT Auth Settings",
				"enabled": 0,
				"enable_login": 1,
				"enable_user_reg": 1,
				"provider": "Cloudflare Access"
			})
			settings.insert(ignore_permissions=True, ignore_mandatory=True)
			frappe.msgprint("JWT Auth Settings created successfully")
		except Exception as e:
			frappe.log_error(f"Error creating JWT Auth Settings: {str(e)}", "JWT Auth Installation")
