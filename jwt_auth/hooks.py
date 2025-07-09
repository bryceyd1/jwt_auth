app_description = "JWT Auth"
app_email = "kevin@avu.nu"
app_license = "mit"
app_name = "jwt_auth"
app_publisher = "Avunu LLC"
app_title = "JWT Auth"
app_version = "0.0.1"

# Required for Frappe Framework integration
required_apps = ["frappe"]

# App installation hooks
after_install = ["jwt_auth.install.after_install"]

# Request and authentication hooks
after_request = ["jwt_auth.auth.handle_redirects"]
# Re-enable auth_hooks with better error handling
auth_hooks = ["jwt_auth.auth.validate_auth"]
on_logout = ["jwt_auth.auth.on_logout"]

# Boot session
boot_session = ["jwt_auth.boot.boot_session"]

# App JavaScript includes
app_include_js = [
    "app.bundle.js"
]

# Document events
doc_events = {
    "Contact": {
        "on_update": "jwt_auth.jwt_auth.hooks.contact.on_update",
    }
}

# Website context modifications
website_context = {
    "post_login": [
        {"label": "My Account", "url": "/me"},
        {"label": "Log out", "url": "/?cmd=jwt_auth.auth.web_logout"}
    ]
}

# Fixtures - data that should be imported during installation
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["dt", "in", ["User", "Contact"]]]
    }
]