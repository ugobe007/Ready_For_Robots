# RFR site design package (2026-10-15)

For copilot. Start with **COPILOT_BUILD_GUIDE.md**.

- `static/` — open `static/Home.html` in a browser; links go between the six pages (first state only, no interactions).
- `shots/` — full-page screenshots at 1440px.
- `design/` — design sources (`.dc.html`): markup plus a `renderVals()` class with sample data and interaction logic. Reference only; rebuild in React in `readyforrobots-new/`.
- `website_copy_v1.md` — approved copy. Where it differs from the designs, the designs win.

Pages: Home, Results, Buyer, Picker, Saved (My desk: Pipeline), Pricing.
Fonts load from Google Fonts; offline you'll see fallbacks.
No secrets are in this package.
