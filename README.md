# JWT Auth for Frappe

**JWT Auth** is a Frappe App that enables authentication via JWT tokens, integrating seamlessly with identity providers like Cloudflare Access. Instead of relying on native Frappe logins, this app authenticates incoming requests against a configured identity provider's JWT token, automatically logging in or registering users as needed.

   - **Enabled:** Check this to enable JWT-based authentication.
   - **Enable Login:** Check to redirect unauthenticated users to the provider's login.
   - **Enable User Reg:** Allow the creation of new users if they do not exist.
   - **Provider:** Select the provider (e.g., "Cloudflare Access" or "Keycloak").
   
   **For Cloudflare Access:**
   - **team_name:** Your Cloudflare Access team name.
   - **aud_tag:** The AUD (audience) tag issued by Cloudflare.
   - **jwt_private_secret:** The expected JWT "audience" or secret used by the JWT library to validate the token's audience.
   
   **For Keycloak:**
   - **keycloak_server_url:** Your Keycloak server URL (e.g., `https://keycloak.example.com`).
   - **keycloak_realm:** The Keycloak realm name.
   - **keycloak_client_id:** The client ID configured in Keycloak.
   - **keycloak_client_secret:** The client secret (optional, for confidential clients).
   
   After saving, your configuration will guide the JWTAuth provider logic.hat enables authentication via JWT tokens, integrating seamlessly with identity providers like Cloudflare Access and Keycloak. Instead of relying on native Frappe logins, this app authenticates incoming requests against a configured identity provider's JWT token, automatically logging in or registering users as needed.

## Features

- **Provider-Based Architecture:**  
  Easily switch between different JWT providers (e.g., Cloudflare Access, Keycloak) by selecting a provider in the **JWT Auth Settings**.
  
- **Automatic Login and Registration:**  
  If the incoming JWT is valid and the user exists, they are immediately logged in. If the user does not exist but user registration is enabled, a new user will be created from existing `Contact` information or a placeholder user will be created, prompting profile updates.
  
- **Customizable Login and Logout URLs:**  
  Providers can define their own login and logout endpoints. This allows deep integration with various identity management and single sign-on (SSO) solutions.

- **OAuth2 Authorization Code Flow:**  
  For providers like Keycloak, supports the standard OAuth2 authorization code flow with automatic token exchange and user information retrieval.
  
- **Flexible Hooks:**  
  - `auth_hooks = ["jwt_auth.auth.validate_auth"]` ensures JWT validation occurs on every request.
  - `on_logout = ["jwt_auth.auth.on_logout"]` allows custom behavior on user logout.
  - A custom `page_renderer` is included to streamline the authentication and redirection flow.

## Prerequisites

- Frappe Framework (v15+ recommended, though it may work on other versions).
- An existing Identity Provider (IdP) that issues JWT tokens, such as Cloudflare Access or Keycloak.
- `requests` Python library (typically included by default in Frappe environments).
  
## Installation

Navigate to your bench directory and install the app:
```bash
bench get-app https://github.com/Avunu/jwt_auth.git
bench --site your-site-name install-app jwt_auth
```

## Configuration

1. **JWT Auth Settings:**  
   In Frappe, open **JWT Auth Settings** from the desk search.  
   
   - **Enabled:** Check this to enable JWT-based authentication.
   - **Enable Login:** Check to redirect unauthenticated users to the provider’s login.
   - **Enable User Reg:** Allow the creation of new users if they do not exist.
   - **Provider:** Select the provider (e.g., "Cloudflare Access").
   
   For **Cloudflare Access**:
   - **team_name:** Your Cloudflare Access team name.
   - **aud_tag:** The AUD (audience) tag issued by Cloudflare.
   - **jwt_private_secret:** The expected JWT "audience" or secret used by the JWT library to validate the token’s audience.
   
   After saving, your configuration will guide the JWTAuth provider logic.

2. **Provider-Specific Fields:**  
   Each provider class handles URL generation, JWKS endpoints, and tokens differently. 
   
   **For Cloudflare Access:**
   - The JWKS URL is automatically derived from `team_name`.
   - The `Cf-Access-Token` header or cookie is used for token retrieval.
   
   **For Keycloak:**
   - The JWKS URL follows the standard OpenID Connect discovery pattern.
   - Uses standard `Authorization: Bearer <token>` header for JWT tokens.
   - Supports OAuth2 authorization code flow for user authentication.
   - Callback URL: `https://your-site.com/api/method/jwt_auth.auth.callback`

3. **Keycloak Client Configuration:**  
   In your Keycloak admin console, create a client with:
   - **Client ID:** Match the `keycloak_client_id` in JWT Auth Settings.
   - **Client Protocol:** `openid-connect`
   - **Access Type:** `public` (for public clients) or `confidential` (if using client secret).
   - **Valid Redirect URIs:** `https://your-frappe-site.com/api/method/jwt_auth.auth.callback`
   - **Web Origins:** `https://your-frappe-site.com`

## Usage

- **Login:**  
  If `Enable Login` is checked and a user hits a page while unauthenticated, they will be redirected to the provider’s login URL.

- **Logout:**  
  Logging out from the Frappe interface or calling `/?cmd=jwt_auth.auth.web_logout` will revoke the session and redirect the user to the provider’s logout URL.

- **Automatic Redirection:**  
  Unauthenticated users are redirected to the login URL. If registration is enabled and the user does not exist, a new user is created and optionally redirected to a profile update page.

## Contributing New Providers

1. Create a new provider class in `jwt_auth/providers.py` inheriting from `BaseProvider`.
2. Implement `get_jwks_url()`, `get_login_url()`, `get_logout_url()`, and any other required properties.
3. Update the **JWT Auth Settings** DocType to include the necessary fields for your new provider.
4. Add logic in `auth.py`’s `get_provider()` method to instantiate your new provider class.

## Troubleshooting

- **Invalid Token Errors:**  
  Check that the `jwt_private_secret` (audience) and provider settings are correct, and that your IdP’s JWKS URL is reachable.

- **Users Not Created:**  
  Make sure `Enable User Reg` is checked and that the user’s email is present in the JWT claims. If user registration logic relies on the `Contact` doctype, ensure `Contact` records exist, or fallback logic creates a placeholder user.

- **Redirect Loops:**  
  If you experience redirect loops, verify that you are receiving a valid token from your IdP. Confirm that the token is set in the correct header or cookie as expected by the provider class.

## License

MIT License. See [LICENSE](./LICENSE) for more details.