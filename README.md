# ePACE DMT Auto

Lightweight Digital Maturity Test — Express version.

Hosted on GitHub Pages: https://domid-epace.github.io/epace-dmt-auto/

## How it works
- Form is embedded in the [ePACE DMT landing page](https://domid-epace.github.io/dashboards/dmt-landing-page.html#dmt-express)
- User fills in their URL + 5 questions + email
- JavaScript scans the URL for tech stack signals (CORS proxy)
- JavaScript calls Anthropic Claude Sonnet API directly
- Result is base64-encoded and appended to the dashboard URL
- Dashboard page decodes and renders the Tier I–IV result

## Dashboard URL format
```
https://domid-epace.github.io/epace-dmt-auto/dashboard.html?r=<base64-result>
```
The URL is fully shareable — all result data is in the URL parameter.

## Configuration
In `dmt-landing-page.html`, set `ANTHROPIC_API_KEY` in the DMT Express script block.
