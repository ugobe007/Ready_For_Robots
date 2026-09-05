# Enable Microsoft 365 (Azure) OAuth for ReadyForRobots

ICP robot OEMs often use Microsoft 365. Signup/Login already call Supabase
`signInWithOAuth({ provider: "azure" })`. The button stays no-op until Azure is
enabled in your Supabase project.

## Steps

1. Azure Portal → App registrations → New registration  
   - Name: `ReadyForRobots`  
   - Supported account types: *Accounts in any organizational directory and personal Microsoft accounts* (or org-only if you prefer)  
   - Redirect URI (Web):  
     `https://<YOUR_SUPABASE_PROJECT_REF>.supabase.co/auth/v1/callback`

2. Certificates & secrets → New client secret → copy the **Value**.

3. Overview → copy **Application (client) ID**.

4. Supabase Dashboard → Authentication → Providers → **Azure**  
   - Enable  
   - Paste Application ID + Client Secret  
   - Save

5. Optional: Authentication → URL Configuration  
   - Site URL: `https://readyforrobots.com`  
   - Redirect allow list: `https://readyforrobots.com/**`, `http://localhost:5173/**`

6. Smoke test: `/signup` → **Continue with Microsoft 365**.

Until this is configured, the UI shows a clear error if Azure is disabled and
users can still use Google or a magic link.
