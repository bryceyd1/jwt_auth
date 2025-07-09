// Copyright (c) 2024, Avunu LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on("JWT Auth Settings", {
	refresh(frm) {
		// Only toggle fields if provider field exists
		if (frm.doc.provider !== undefined) {
			toggle_provider_fields(frm);
		}
	},

	provider(frm) {
		toggle_provider_fields(frm);
	}
});

function toggle_provider_fields(frm) {
	const provider = frm.doc.provider;
	
	// Check if fields exist before trying to toggle them
	const hasCloudflareFields = frm.fields_dict.team_name && frm.fields_dict.aud_tag;
	const hasKeycloakFields = frm.fields_dict.keycloak_server_url && frm.fields_dict.keycloak_realm;
	
	if (hasCloudflareFields) {
		// Show/hide Cloudflare Access fields
		frm.toggle_display("cloudflare_section", provider === "Cloudflare Access");
		frm.toggle_display("team_name", provider === "Cloudflare Access");
		frm.toggle_display("aud_tag", provider === "Cloudflare Access");
		
		// Update field requirements
		frm.toggle_reqd("team_name", provider === "Cloudflare Access");
		frm.toggle_reqd("aud_tag", provider === "Cloudflare Access");
	}
	
	if (hasKeycloakFields) {
		// Show/hide Keycloak fields
		frm.toggle_display("keycloak_section", provider === "Keycloak");
		frm.toggle_display("keycloak_server_url", provider === "Keycloak");
		frm.toggle_display("keycloak_realm", provider === "Keycloak");
		frm.toggle_display("keycloak_client_id", provider === "Keycloak");
		frm.toggle_display("keycloak_client_secret", provider === "Keycloak");
		
		// Update field requirements
		frm.toggle_reqd("keycloak_server_url", provider === "Keycloak");
		frm.toggle_reqd("keycloak_realm", provider === "Keycloak");
		frm.toggle_reqd("keycloak_client_id", provider === "Keycloak");
	}
}
