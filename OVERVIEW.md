# DMT Auto — Project Overview & Working Document

> **Status:** MVP live on GitHub Pages — API key baked in, no user prompt
> **Last updated:** 2026-04-23
> **Repo:** [domid-epace/epace-dmt-auto](https://github.com/domid-epace/epace-dmt-auto)
> **Landing page:** [domid-epace/dashboards](https://github.com/domid-epace/dashboards) → `dmt-landing-page.html`

---

## What is DMT Auto?

DMT Auto is a lightweight, public-facing version of ePACE's Digital Maturity Test. Unlike the full `dmt-ai` tool (which runs a 4-day automated customer journey with Playwright), DMT Auto:

- Takes **URL input** (1 site + up to 2 competitors)
- Scans the **HTML source** for tech stack signals (factual, no hallucination)
- Asks **5 free-text questions** answered by the user
- Scores everything via **Claude Sonnet API**
- Returns a **Tier I–IV** result (not a 0–100 score)
- Shows results on a **shareable dashboard URL**

Target use: presales lead generation, embedded on the ePACE website.

---

## Live URLs

| What | URL |
|---|---|
| Landing page (with form) | `https://domid-epace.github.io/dashboards/dmt-landing-page.html` |
| Results dashboard | `https://domid-epace.github.io/epace-dmt-auto/dashboard.html?r=<base64>` |
| Repo — backend + dashboard | `https://github.com/domid-epace/epace-dmt-auto` |
| Repo — landing page | `https://github.com/domid-epace/dashboards` |

---

## Tier System

| Tier | Label | Score range | Description |
|---|---|---|---|
| I | Digital Infant | 0–25 | Minimal tech, no systematic data collection, ad-hoc comms |
| II | Digital Aware | 26–50 | Tools exist but disconnected; email works, no real automation |
| III | Digital Active | 51–75 | Connected stack, basic automation, systematic data collection |
| IV | Digital Mature | 76–100 | Personalization at scale, omnichannel, data-driven decisions |

---

## Architecture (MVP — GitHub Pages)

```
dmt-landing-page.html           (domid-epace/dashboards)
  └── DMT Express form (inline JS)
        ├── Step 1: URL + 2 optional competitors
        ├── Steps 2–6: 5 free-text questions
        ├── Step 7: name + email
        └── Submit:
              ├── scanUrl(url) → fetches HTML via corsproxy.io → detects tools
              ├── callAnthropic(prompt) → Claude Sonnet API (browser-side)
              └── redirect → dashboard.html?r=<base64-JSON>

dashboard.html                  (domid-epace/epace-dmt-auto)
  └── decodes ?r= param → renders Tier card + tools + strengths/gaps + next step + share button
```

### Key JS variables in `dmt-landing-page.html`

```javascript
const DMT_DASHBOARD_URL  = 'https://domid-epace.github.io/epace-dmt-auto/dashboard.html';
const ANTHROPIC_API_KEY  = '__DMT_API_KEY__';  // placeholder — injected at deploy time
const ANTHROPIC_MODEL    = 'claude-sonnet-4-6';
const CORS_PROXY         = 'https://corsproxy.io/?';
```

### Base64 encoding — UTF-8 fix

`btoa()` only handles Latin1. Czech characters in Claude's response caused a crash.
Fixed with:

```javascript
// Encode (landing page)
const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(result))));

// Decode (dashboard)
JSON.parse(decodeURIComponent(escape(atob(raw))))
```

---

## API Key — Current Situation

### How it works (live)

The API key is **never committed to git**. It lives in a GitHub Actions secret (`DMT_API_KEY`).

Deployment flow:
1. Push to `main` triggers `.github/workflows/deploy.yml` in `domid-epace/dashboards`
2. `sed` replaces `__DMT_API_KEY__` with the secret value in the HTML
3. `actions/upload-pages-artifact` + `actions/deploy-pages` publishes via GitHub Pages API (no git commit → bypasses push protection scanner)
4. Users get the page with the real key already baked in — no prompt

To update the key:
```
curl -X PUT \
  -H "Authorization: token <domid-epace-token>" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/domid-epace/dashboards/actions/secrets/DMT_API_KEY" \
  -d '{"encrypted_value":"<encrypted>","key_id":"<id>"}'
```
Or update via GitHub UI: Settings → Secrets and variables → Actions → `DMT_API_KEY`.
Then run the workflow manually (Actions → Deploy to GitHub Pages → Run workflow).

### Production path options

| Option | Effort | When |
|---|---|---|
| **Cloudflare Worker proxy** | Low (1–2h) | Before going public on epace.cz |
| **Flask backend on Render/Railway** | Medium (half day) | If lead persistence + email delivery needed |

**Cloudflare Worker approach (recommended for public launch):**
```
browser → POST https://dmt-proxy.epace.workers.dev/assess → Worker → Anthropic API
```
- Key lives in Cloudflare env vars (not in git)
- CORS enabled, no proxy issues
- Free up to 100k requests/day

---

## The 5 Questions

| # | Topic | Intent |
|---|---|---|
| Q1 | Marketingová databáze | Size + collection method → Consent & Capture signal |
| Q2 | Email marketing a automatizace | Flows, welcome, cart abandonment → Email chapter |
| Q3 | Personalizace | Segments, dynamic content, recommendations → Web Personalization chapter |
| Q4 | Zákaznická data — propojení a objem | Data unification — siloed or unified? → CDP readiness signal |
| Q5 | Emailová automatizace a metriky | Behavioral triggers + open rate metrics → Timing chapter |

Q4 and Q5 replaced original "marketing tools" and "goal/challenge" questions — the HTML scan already covers tools, and CDP interest is assumed context.

---

## Tech Stack Detection (30+ signals)

Detected from HTML source via regex — **no inference, no hallucination**:

- **Analytics:** GA4, GTM
- **CDP/ESP:** Bloomreach, Klaviyo, Emarsys, Salesforce MC, Mailchimp, Dotdigital
- **Reco engines:** Luigi's Box, Klevu, Nosto
- **CMP/Consent:** Cookiebot, OneTrust, CookiePro, Usercentrics
- **Advertising:** Meta Pixel, TikTok Pixel, Google Ads
- **Heatmaps:** Hotjar, Microsoft Clarity
- **Chat:** Intercom, Zendesk, Tidio, LiveChat, Tawk.to
- **Other:** Segment, Meiro, Optimizely, VWO, PWA/Service Worker
- **Heuristics:** newsletter form, cookie banner, mobile app links, loyalty program, cart

---

## Python Backend (Production Path)

The repo also contains a Flask backend (`app.py`, `scanner.py`, `scorer.py`) for when the client-side approach is replaced. When deployed to a server:

1. Set `DMT_DASHBOARD_URL` to a server-rendered results page instead of GitHub Pages
2. Move `ANTHROPIC_API_KEY` to `.env` (server-side — not exposed to browser)
3. URL scanning runs via `requests` (no CORS proxy needed)

```bash
cd epace-dmt-auto
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
python app.py          # runs on port 5050
```

Endpoint: `POST /api/assess` — body: `{ url, answers[5], email, name?, competitors[] }`

---

## Open Items / Next Steps

- [ ] **CORS proxy reliability** — `corsproxy.io` is a free public service. Cloudflare Worker would replace this and also solve the key exposure issue.
- [ ] **Email delivery** — currently results only shown in browser. Should the user receive results by email too?
- [ ] **Lead persistence** — email + tier not stored in MVP (client-side only). Flask backend (`app.py`) saves to `leads.csv` when deployed.
- [ ] **Competitor scoring** — competitor URLs are collected but not yet scored. Backend has the plumbing ready.
- [ ] **Results page: radar chart** — consider adding Chart.js radar across 5 dimensions for visual richness.
- [ ] **Connect to full DMT** — after Tier II–III result, upsell path to paid ePACE Digital Maturity Assessment (1 499 €).
- [ ] **Move to epace.cz** — when ready to go public, host under epace.cz domain.

---

## Relation to dmt-ai (Full Tool)

| | dmt-ai | dmt-auto |
|---|---|---|
| Input | URL + shopping intention | URL + 5 questions |
| Method | 4-day Playwright simulation | HTML scan + user answers |
| Output | 0–100 score, 8 chapters, 44 questions | Tier I–IV, 5 signals |
| Time | ~45 min/target | ~15 sec |
| Reliability | Medium (Playwright flaky, email timing) | High (no simulation) |
| Use case | Deep presales audit (internal) | Public lead gen + quick screening |
| API key exposure | Server-side (.env) | GitHub Actions secret → baked at deploy |

---

## File Map

```
dmt-auto/ (local: OneDrive/Claude-ePACE/dmt-auto/)
├── OVERVIEW.md          ← this file
├── app.py               ← Flask backend
├── scanner.py           ← HTML tech stack scanner
├── scorer.py            ← Claude Sonnet scorer
├── config.py            ← env vars
├── requirements.txt
└── .env.example

GitHub repos:
├── domid-epace/epace-dmt-auto/
│   ├── dashboard.html   ← results page (GitHub Pages)
│   ├── app.py           ← Flask backend copy
│   ├── scanner.py
│   └── scorer.py
│
└── domid-epace/dashboards/
    ├── .github/workflows/deploy.yml  ← GH Actions: injects key + deploys
    └── dmt-landing-page.html         ← landing page with DMT Express form
```
