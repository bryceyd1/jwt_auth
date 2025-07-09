// JWT Auth App Bundle - Override logout functionality
// Simplified version to prevent conflicts with Frappe core

window.jwt_auth = window.jwt_auth || {};

window.jwt_auth.init = function() {
	// Wait for frappe to be fully initialized
	if (window.frappe && window.frappe.app && window.frappe.app.logout && !window.jwt_auth.initialized) {
		console.log('JWT Auth: Initializing logout override');
		
		// Store reference to original logout function
		const originalLogout = frappe.app.logout.bind(frappe.app);

		// Override the logout function to use JWT Auth logout
		frappe.app.logout = function() {
			const me = this;
			me.logged_out = true;

			return frappe.call({
				method: "jwt_auth.auth.jwt_logout",
				callback: function(r) {
					if (r.exc) {
						console.error('JWT Auth logout error:', r.exc);
						// Fall back to original logout if JWT logout fails
						originalLogout();
						return;
					}
					if (r.message && r.message.redirect_url) {
						window.location.href = r.message.redirect_url;
					} else {
						me.redirect_to_login();
					}
				},
				error: function(err) {
					console.error('JWT Auth logout call failed:', err);
					// Fall back to original logout on error
					originalLogout();
				}
			});
		};

		window.jwt_auth.initialized = true;
		console.log('JWT Auth: Logout function overridden successfully');
	}
};

// Try to initialize when the script loads
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', function() {
		// Try initializing with a slight delay to ensure frappe is ready
		setTimeout(window.jwt_auth.init, 100);
	});
} else {
	// DOM is already ready, try initializing with a delay
	setTimeout(window.jwt_auth.init, 100);
}

// Also try on frappe ready
if (window.frappe && window.frappe.ready) {
	frappe.ready(function() {
		setTimeout(window.jwt_auth.init, 50);
	});
} else {
	// Frappe might not be loaded yet, set up a listener
	document.addEventListener('frappe:ready', function() {
		setTimeout(window.jwt_auth.init, 50);
	});
}