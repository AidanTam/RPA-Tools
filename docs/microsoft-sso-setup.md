# Microsoft (Entra ID) SSO setup — SLR Tools

This app can require **Microsoft sign-in**, restricted to the **SLR Entra directory**,
so only SLR employees can use it. It uses Streamlit's native OpenID Connect support
(`st.login` / `st.user`) with a **single-tenant** Entra app registration.

The app code is already wired for this. It stays on the old shared passphrase until
the `[auth]` secrets below are added — the moment they are present, SSO takes over
automatically (no code change or redeploy needed).

**Who does this:** someone with **Entra ID app-registration rights** (IT / tenant admin)
plus access to the app's **Streamlit Cloud → Settings → Secrets**.

---

## 1. Register the app in Entra ID

Azure Portal → **Microsoft Entra ID** → **App registrations** → **New registration**.

- **Name:** `SLR Tools`
- **Supported account types:** **Accounts in this organizational directory only (Single tenant)**
  — this is what limits access to SLR employees.
- **Redirect URI:** platform **Web**, value:
  ```
  https://rpa-tools-lgtdu6uyh9sykzia3u3trw.streamlit.app/oauth2callback
  ```
  (If you also run it locally for testing, add a second Web redirect URI:
  `http://localhost:8501/oauth2callback`.)

Click **Register**.

From the app's **Overview** page, copy:
- **Application (client) ID**
- **Directory (tenant) ID**

## 2. Create a client secret

App → **Certificates & secrets** → **Client secrets** → **New client secret**.
- Description: `SLR Tools Streamlit`
- Expiry: pick a policy-compliant lifetime (max 24 months).
- **Copy the secret `Value`** (not the Secret ID) immediately — it's only shown once.

> ⚠️ Client secrets expire. Put a reminder to rotate it before the expiry date, or
> the app will stop letting anyone in. Rotating = create a new secret, update the
> Streamlit secret, delete the old one.

## 3. (Optional) API permissions

The default delegated **`User.Read`** / OpenID permissions (`openid`, `profile`,
`email`) are enough for sign-in. No admin consent beyond the defaults is required
for basic authentication.

## 4. Add the secrets in Streamlit Cloud

Streamlit Cloud → the SLR Tools app → **Settings** → **Secrets**, and add:

```toml
[auth]
redirect_uri = "https://rpa-tools-lgtdu6uyh9sykzia3u3trw.streamlit.app/oauth2callback"
cookie_secret = "PASTE_A_LONG_RANDOM_STRING"
client_id = "APPLICATION_CLIENT_ID_FROM_STEP_1"
client_secret = "CLIENT_SECRET_VALUE_FROM_STEP_2"
server_metadata_url = "https://login.microsoftonline.com/DIRECTORY_TENANT_ID/v2.0/.well-known/openid-configuration"
```

Notes:
- `cookie_secret` — any long random string (it signs the login cookie). Generate one with:
  `python -c "import secrets; print(secrets.token_hex(32))"`
- `server_metadata_url` — must contain your **tenant ID** (not `common` or `organizations`).
  Using the tenant-specific URL is what enforces single-tenant / SLR-only sign-in.

Save. Streamlit will restart the app; it now shows **"Log in with Microsoft."**

## 5. Verify

- Open the app → click **Log in with Microsoft** → sign in with an SLR account → you should
  land on the app, with **"Signed in as …"** and a **Log out** button in the sidebar.
- Try a personal / non-SLR Microsoft account → it should be **rejected** (not in the tenant).

## 6. Finish the cutover

Once a real employee sign-in is confirmed:
- **Delete the old `APP_PASSWORD`** secret (and the `SLR123` default is dead code once SSO is live).
- Tell the maintainer so the passphrase fallback can be removed from `rpa_tools.py`.

---

## Tightening later (optional)

To restrict beyond "anyone in the SLR directory" (e.g. only a Resource Geology group):
- Entra → **Enterprise applications** → SLR Tools → **Properties** → **Assignment required = Yes**,
  then **Users and groups** → assign the specific people/groups. Only assigned users can sign in.
- (A code-side email-domain or group-claim check can be added too if wanted — ask the maintainer.)
