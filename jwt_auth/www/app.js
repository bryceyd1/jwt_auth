// JWT Auth Web Context Handler
// This file provides additional web context for the app

frappe.ready(function() {
	// Ensure JWT Auth is properly initialized for web pages
	if (window.frappe && window.frappe.session && window.frappe.session.user === 'Guest') {
		// Check if JWT authentication should redirect
		// This is handled server-side, but we can add client-side checks here if needed
	}
});
