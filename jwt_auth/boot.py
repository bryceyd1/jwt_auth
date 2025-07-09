import frappe

def boot_session(bootinfo):
	"""Add JWT Auth configuration to boot info for the session"""
	try:
		# Only add JWT auth info if settings exist
		if frappe.db.exists("JWT Auth Settings", "JWT Auth Settings"):
			settings = frappe.get_cached_doc("JWT Auth Settings")
			bootinfo.jwt_auth = {
				"enabled": getattr(settings, 'enabled', False),
				"enable_login": getattr(settings, 'enable_login', False),
				"provider": getattr(settings, 'provider', 'Cloudflare Access')
			}
	except Exception as e:
		# Don't let boot session fail because of JWT Auth
		frappe.log_error(f"JWT Auth boot session error: {str(e)}", "JWT Auth Boot Error")
		bootinfo.jwt_auth = {"enabled": False}
