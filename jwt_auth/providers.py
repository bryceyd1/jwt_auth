import json
import jwt
import requests
from urllib.parse import quote, urlencode

import frappe

class BaseProvider:
    """A base class/interface for authentication providers."""
    
    def __init__(self, settings):
        self.settings = settings

    @property
    def enabled(self):
        return self.settings.enabled

    @property
    def enable_login(self):
        return self.settings.enable_login

    @property
    def enable_user_reg(self):
        return self.settings.enable_user_reg

    @property
    def jwt_private_secret(self):
        return self.settings.get_password("jwt_private_secret")

    @property
    def jwt_header(self):
        # For Cloudflare Access tokens, we'll override this in the subclass if needed.
        return "Cf-Access-Token"

    def get_login_url(self, redirect_to=None):
        """Return a constructed login URL for this provider."""
        raise NotImplementedError

    def get_logout_url(self):
        """Return a constructed logout URL for this provider."""
        raise NotImplementedError

    def get_jwks_url(self):
        """Return the JWKS URL for this provider."""
        raise NotImplementedError

    def get_public_keys(self):
        """Retrieve and return public keys for JWT verification."""
        r = requests.get(self.get_jwks_url())
        jwk_set = r.json()
        public_keys = []
        for key_dict in jwk_set["keys"]:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_dict))
            public_keys.append(public_key)
        return public_keys


class CloudflareAccessProvider(BaseProvider):
    """Cloudflare Access Provider Implementation.
    Requires 'team_name' and 'aud_tag' fields in JWT Auth Settings.
    Redirect parameters are fixed:
    - Frappe uses `redirect-to` internally.
    - Cloudflare Access expects `redirect_url`.
    """

    @property
    def team_name(self):
        return self.settings.team_name

    @property
    def aud_tag(self):
        return self.settings.aud_tag

    @property
    def jwt_header(self):
        # Cloudflare Access typically passes tokens in `Cf-Access-Token` headers or cookies
        return "Cf-Access-Token"

    def get_jwks_url(self):
        # Cloudflare Access JWKS URL:
        return f"https://{self.team_name}.cloudflareaccess.com/cdn-cgi/access/certs"

    def get_login_url(self, redirect_to=None):
        # Cloudflare Access login URL:
        # Example: https://<team_name>.cloudflareaccess.com/cdn-cgi/access/login/<aud_tag>
        login_url = f"https://{self.team_name}.cloudflareaccess.com/cdn-cgi/access/login/{self.aud_tag}"

        # If we have a frappe redirect-to parameter, we translate it into cloudflare's `redirect_url`.
        # `redirect_to` is what frappe uses internally. We know cloudflare expects `redirect_url`.
        if redirect_to:
            path = '%2F' + quote(redirect_to, safe='')
            login_url += f"?redirect_url={path}"

        return login_url

    def get_logout_url(self):
        # Cloudflare Access logout URL:
        # https://<team_name>.cloudflareaccess.com/cdn-cgi/access/logout
        logout_url = f"https://{self.team_name}.cloudflareaccess.com/cdn-cgi/access/logout"

        # After logout, redirect user back to the frappe site homepage or a known URL.
        # Cloudflare expects `redirect_url` param.
        site_url = frappe.utils.get_url()
        logout_url += f"?redirect_url={quote(site_url, safe='')}"

        return logout_url


class KeycloakProvider(BaseProvider):
    """Keycloak Provider Implementation.
    Requires 'keycloak_server_url', 'keycloak_realm', and 'keycloak_client_id' fields in JWT Auth Settings.
    """

    @property
    def keycloak_server_url(self):
        return self.settings.keycloak_server_url.rstrip('/')

    @property
    def keycloak_realm(self):
        return self.settings.keycloak_realm

    @property
    def keycloak_client_id(self):
        return self.settings.keycloak_client_id

    @property
    def jwt_header(self):
        # Keycloak typically uses standard Authorization header with Bearer token
        return "Authorization"

    def get_jwks_url(self):
        # Keycloak JWKS URL:
        return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    def get_login_url(self, redirect_to=None):
        # Keycloak OAuth2/OIDC authorization endpoint
        auth_url = f"{self.keycloak_server_url}/realms/{self.keycloak_realm}/protocol/openid-connect/auth"
        
        # Build redirect URI - this should be your callback endpoint
        site_url = frappe.utils.get_url()
        redirect_uri = f"{site_url}/api/method/jwt_auth.auth.callback"
        
        # If we have a specific redirect_to, we can pass it as state parameter
        params = {
            'client_id': self.keycloak_client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email',
        }
        
        if redirect_to:
            params['state'] = redirect_to
            
        return f"{auth_url}?{urlencode(params)}"

    def get_logout_url(self):
        # Keycloak logout endpoint
        logout_url = f"{self.keycloak_server_url}/realms/{self.keycloak_realm}/protocol/openid-connect/logout"
        
        # Redirect back to site after logout
        site_url = frappe.utils.get_url()
        params = {
            'redirect_uri': site_url
        }
        
        return f"{logout_url}?{urlencode(params)}"

    def get_token_url(self):
        """Return the token endpoint for OAuth2 code exchange."""
        return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}/protocol/openid-connect/token"

    def exchange_code_for_token(self, code, redirect_uri):
        """Exchange authorization code for access token."""
        token_url = self.get_token_url()
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.keycloak_client_id,
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        # If you have a client secret, add it here
        client_secret = self.settings.get_password("keycloak_client_secret")
        if client_secret:
            data['client_secret'] = client_secret
            
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        return response.json()

    def get_userinfo(self, access_token):
        """Get user information from Keycloak userinfo endpoint."""
        userinfo_url = f"{self.keycloak_server_url}/realms/{self.keycloak_realm}/protocol/openid-connect/userinfo"
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(userinfo_url, headers=headers)
        response.raise_for_status()
        
        return response.json()