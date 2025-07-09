import frappe

def execute():
	"""Set default provider for existing JWT Auth Settings"""
	try:
		if frappe.db.exists("JWT Auth Settings", "JWT Auth Settings"):
			doc = frappe.get_doc("JWT Auth Settings", "JWT Auth Settings")
			
			# Set default provider if not already set
			if not hasattr(doc, 'provider') or not doc.provider:
				doc.provider = "Cloudflare Access"
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				print("Updated JWT Auth Settings with default provider")
	except Exception as e:
		print(f"Error in patch: {str(e)}")
		# Don't fail the patch, just log the error
		frappe.log_error(f"JWT Auth patch error: {str(e)}", "JWT Auth Patch")
