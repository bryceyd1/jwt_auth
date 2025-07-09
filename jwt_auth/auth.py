import frappe
import json
import jwt
import requests
from urllib.parse import quote
from jwt_auth.providers import CloudflareAccessProvider, KeycloakProvider

class SessionJWTAuth:
    def __init__(self, path=None, http_status_code=None):
        if not hasattr(frappe.local, "jwt_auth"):
            frappe.local.jwt_auth = JWTAuth(path, http_status_code)
        elif path or http_status_code:
            frappe.local.jwt_auth.update(path, http_status_code)

    def __getattr__(self, name):
        return getattr(frappe.local.jwt_auth, name)


class JWTAuth:
    def __init__(self, path=None, http_status_code=None):
        self.path = path
        self.http_status_code = http_status_code
        self.settings = None
        self.provider = None
        self.claims = None
        self.user_email = None
        self.token = None
        self.redirect_to = None
        
        # Initialize with error handling
        try:
            self.settings = frappe.get_cached_doc("JWT Auth Settings")
            self.provider = self.get_provider()
        except Exception as e:
            frappe.log_error(f"JWT Auth initialization error: {str(e)}", "JWT Auth Error")
            # Set to disabled state if we can't load settings
            self.settings = type('MockSettings', (), {'enabled': False})()
            self.provider = None

    def get_provider(self):
        """Get the appropriate provider based on settings."""
        try:
            if not self.settings:
                return None
                
            provider_name = getattr(self.settings, 'provider', 'Cloudflare Access')
            
            if provider_name == 'Keycloak':
                return KeycloakProvider(self.settings)
            else:
                # Default to Cloudflare Access
                return CloudflareAccessProvider(self.settings)
        except Exception as e:
            frappe.log_error(f"JWT Provider initialization error: {str(e)}", "JWT Auth Error")
            return None

    def auth(self):
        self.user_email = self.claims.get("email") if self.claims.get("email") else None
        if not self.user_email:
            return
        user_email = self.claims.get("email") if self.claims.get("email") else None
        if user_email:
            Contact = frappe.qb.DocType("Contact")
            ContactEmail = frappe.qb.DocType("Contact Email")
            user_exists = (
                frappe.qb.from_(Contact)
                .select("user")
                .join(ContactEmail)
                .on(Contact.name == ContactEmail.parent)
                .where(ContactEmail.email_id == user_email)
            ).run(as_dict=True)
            if user_exists and user_exists[0].get('user', False):
                frappe.local.login_manager.login_as(user_exists[0].get("user"))
            elif self.settings.enable_user_reg:
                self.register_user(user_email)
                frappe.local.login_manager.login_as(user_email)
                if self.redirect_to:
                    frappe.session.data["jwt_auth_redirect"] = self.redirect_to
                    frappe.cache().set_value(f"jwt_original_location_{user_email}",frappe.local.request.path)

    def validate_auth(self):
        if self.can_auth():
            self.auth()

    def can_auth(self):
        try:
            if self.redirect_to:
                return False
            if frappe.local.session.user and frappe.local.session.user != "Guest":
                return False
            if not self.settings or not self.settings.enabled:
                return False
            if frappe.flags.get("jwt_logout_redirect", False):
                return False
            if not self.provider:
                return False
            
            # For Keycloak OAuth2 flow, check if we're already in an authentication flow
            provider_name = getattr(self.settings, 'provider', 'Cloudflare Access')
            if provider_name == 'Keycloak':
                # For Keycloak, we might not have a direct JWT token in headers
                # Instead, users go through OAuth2 flow
                self.token = self.get_token(frappe.local.request)
                if self.token and self.is_valid_token(self.token):
                    return True
                # If no valid token, user will be redirected to login
                return False
            else:
                # For Cloudflare Access and other direct JWT providers
                self.token = self.get_token(frappe.local.request)
                if not self.token:
                    return False
                if self.is_valid_token(self.token):
                    return True
        except Exception as e:
            frappe.log_error(f"JWT can_auth error: {str(e)}", "JWT Auth Error")
            return False

    def update(self, path, http_status_code):
        self.path = path
        self.http_status_code = http_status_code
        # Refresh provider in case settings changed
        self.provider = self.get_provider()

    def get_login_url(self, redirect_to=None):
        """Get login URL from the provider."""
        return self.provider.get_login_url(redirect_to or self.path)

    def get_logout_url(self):
        """Get logout URL from the provider."""
        return self.provider.get_logout_url()

    def get_public_keys(self):
        """Get public keys from the provider."""
        return self.provider.get_public_keys()

    def get_token(self, request):
        """Get token from request using provider's header."""
        header_name = self.provider.jwt_header
        
        # Handle Authorization header specially for Bearer tokens
        if header_name == "Authorization":
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header[7:]  # Remove "Bearer " prefix
            return None
        
        # For other headers (like Cf-Access-Token), check both cookies and headers
        token = (
            request.cookies.get(header_name)
            if request.cookies.get(header_name)
            else (
                request.headers.get(header_name)
                if request.headers.get(header_name)
                else None
            )
        )
        return token

    def is_valid_token(self, token):
        keys = self.get_public_keys()
        secret = self.provider.jwt_private_secret
        valid_token = False
        
        # Try different algorithms that providers might use
        algorithms = ["RS256", "HS256", "ES256"]
        
        for key in keys:
            for algorithm in algorithms:
                try:
                    # For Keycloak, we might not need audience validation in some cases
                    decode_options = {
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_nbf": True,
                        "verify_iat": True,
                        "verify_aud": bool(secret)  # Only verify audience if secret is provided
                    }
                    
                    if secret:
                        self.claims = jwt.decode(
                            token,
                            key=key,
                            audience=secret,
                            algorithms=[algorithm],
                            options=decode_options
                        )
                    else:
                        self.claims = jwt.decode(
                            token,
                            key=key,
                            algorithms=[algorithm],
                            options=decode_options
                        )
                    valid_token = True
                    break
                except jwt.InvalidTokenError:
                    continue
                except Exception as e:
                    frappe.log_error(f"JWT validation error: {str(e)}", "JWT Auth")
                    continue
            if valid_token:
                break
        return valid_token

    def register_user(self, user_email):
        contact = frappe.db.get_value(
            "Contact Email", {"email_id": user_email}, "parent"
        )

        if contact:
            contact = frappe.get_doc("Contact", contact)
            user = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": user_email,
                    "username": user_email,
                    "first_name": contact.first_name or "[Change Me]",
                    "middle_name": contact.middle_name,
                    "last_name": contact.last_name,
                    "full_name": contact.full_name,
                    "phone": contact.phone,
                    "mobile_no": contact.mobile_no,
                    "gender": contact.gender,
                    "send_welcome_email": 0,
                    "company_name": contact.company_name,
                }
            )
            user.insert(ignore_permissions=True)

            contact.user = user_email
            contact.save(ignore_permissions=True)

            if not contact.first_name:
                self.redirect_to = f"/update-profile/{user_email}/edit"
        else:
            user = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": user_email,
                    "first_name": "[Change Me]",
                    "send_welcome_email": 0,
                }
            )
            user.insert(ignore_permissions=True)

            self.redirect_to = f"/update-profile/{user_email}/edit"

        frappe.db.commit()

    def register_user_from_userinfo(self, user_email, userinfo):
        """Register a new user from Keycloak userinfo."""
        contact = frappe.db.get_value(
            "Contact Email", {"email_id": user_email}, "parent"
        )

        if contact:
            contact = frappe.get_doc("Contact", contact)
            user = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": user_email,
                    "username": user_email,
                    "first_name": userinfo.get("given_name") or contact.first_name or "[Change Me]",
                    "last_name": userinfo.get("family_name") or contact.last_name,
                    "full_name": userinfo.get("name") or contact.full_name,
                    "phone": contact.phone,
                    "mobile_no": contact.mobile_no,
                    "gender": contact.gender,
                    "send_welcome_email": 0,
                    "company_name": contact.company_name,
                }
            )
            user.insert(ignore_permissions=True)

            contact.user = user_email
            contact.save(ignore_permissions=True)

            if not userinfo.get("given_name") and not contact.first_name:
                self.redirect_to = f"/update-profile/{user_email}/edit"
        else:
            user = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": user_email,
                    "first_name": userinfo.get("given_name") or "[Change Me]",
                    "last_name": userinfo.get("family_name"),
                    "full_name": userinfo.get("name"),
                    "send_welcome_email": 0,
                }
            )
            user.insert(ignore_permissions=True)

            if not userinfo.get("given_name"):
                self.redirect_to = f"/update-profile/{user_email}/edit"

        frappe.db.commit()


def handle_redirects(response=None, request=None):
    if not response or not hasattr(frappe, "session"):
        return
    
    if frappe.session.get("user") == "Guest" and frappe.flags.get("jwt_logout_redirect"):
        response.status_code = 302
        response.headers["Location"] = frappe.flags.pop("jwt_logout_redirect")
        return

    redirect_to = frappe.session.data.pop("jwt_auth_redirect", False)
    if not redirect_to and request.path == "/me":
        cache_key = f"jwt_original_location_{frappe.session.user}"
        redirect_to = frappe.cache().get_value(cache_key)
        frappe.cache().delete_value(cache_key)
    if redirect_to:
        response.status_code = 302
        response.headers["Location"] = redirect_to

    return


@frappe.whitelist()
def jwt_logout():
    auth = SessionJWTAuth()
    frappe.local.login_manager.logout()
    if auth.settings.enabled:
        return {"redirect_url": auth.get_logout_url()}
    else:
        return {"redirect_url": "/login"}


@frappe.whitelist()
def on_logout():
    auth = SessionJWTAuth()
    frappe.flags["jwt_logout_redirect"] = auth.get_logout_url()


@frappe.whitelist()
def web_logout():
    auth = SessionJWTAuth()
    frappe.local.login_manager.logout()
    if auth.settings.enabled:
        location = auth.get_logout_url()
    else:
        location = "/login"
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = location


@frappe.whitelist()
def callback():
    """Handle OAuth2 callback from Keycloak."""
    auth = SessionJWTAuth()
    
    # Only handle Keycloak callbacks
    if getattr(auth.settings, 'provider', 'Cloudflare Access') != 'Keycloak':
        frappe.throw("Invalid callback for current provider")
    
    provider = auth.provider
    code = frappe.local.request.args.get('code')
    state = frappe.local.request.args.get('state')
    error = frappe.local.request.args.get('error')
    
    if error:
        frappe.throw(f"OAuth2 error: {error}")
    
    if not code:
        frappe.throw("No authorization code received")
    
    try:
        # Exchange code for tokens
        site_url = frappe.utils.get_url()
        redirect_uri = f"{site_url}/api/method/jwt_auth.auth.callback"
        token_response = provider.exchange_code_for_token(code, redirect_uri)
        
        # Get user info using access token
        access_token = token_response.get('access_token')
        if access_token:
            userinfo = provider.get_userinfo(access_token)
            user_email = userinfo.get('email')
            
            if user_email:
                # Check if user exists
                Contact = frappe.qb.DocType("Contact")
                ContactEmail = frappe.qb.DocType("Contact Email")
                user_exists = (
                    frappe.qb.from_(Contact)
                    .select("user")
                    .join(ContactEmail)
                    .on(Contact.name == ContactEmail.parent)
                    .where(ContactEmail.email_id == user_email)
                ).run(as_dict=True)
                
                if user_exists and user_exists[0].get('user', False):
                    frappe.local.login_manager.login_as(user_exists[0].get("user"))
                elif auth.settings.enable_user_reg:
                    auth.register_user_from_userinfo(user_email, userinfo)
                    frappe.local.login_manager.login_as(user_email)
                else:
                    frappe.throw("User registration is disabled")
                
                # Redirect to original page or state
                redirect_to = state or "/"
                frappe.local.response["type"] = "redirect"
                frappe.local.response["location"] = redirect_to
            else:
                frappe.throw("No email found in user info")
        else:
            frappe.throw("No access token received")
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Keycloak OAuth2 Callback Error")
        frappe.throw(f"Authentication failed: {str(e)}")


def validate_auth():
    """Main authentication validation function called by Frappe hooks."""
    try:
        # Only run if we have a valid request context
        if not hasattr(frappe.local, 'request') or not frappe.local.request:
            return
            
        # Skip validation for static assets and system endpoints
        if frappe.local.request.path.startswith(('/assets/', '/files/', '/private/', '/api/method/frappe.')):
            return
            
        # Initialize and validate JWT authentication
        SessionJWTAuth().validate_auth()
    except Exception as e:
        # Log the error but don't break the application
        frappe.log_error(f"JWT Auth validation error: {str(e)}", "JWT Auth Error")
        # Don't re-raise the exception to avoid breaking the application
