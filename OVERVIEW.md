# DMT Auto — Project Overview & Working Document

> **Status:** MVP live on GitHub Pages  
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
const ANTHROPIC_API_KEY  = 'sk-ant-...';   // ← set here
const ANTHROPIC_MODEL    = 'claude-sonnet-4-6';
const CORS_PROXY         = 'https://corsproxy.io/?';
```

---

## The 5 Questions

| # | Topic | Intent |
|---|---|---|
| Q1 | Marketingová databáze | Size + collection method → Consent & Capture signal |
| Q2 | Email marketing a automatizace | Flows, welcome, cart abandonment → Email chapter |
| Q3 | Personalizace | Segments, dynamic content, recommendations |
| Q4 | Marketingové nástroje (interní) | Internal tools not visible from HTML scan |
| Q5 | Hlavní cíl a výzva | Business context → calibrates scoring + feeds ePACE conversation |

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

- [ ] **Email delivery** — currently results only shown in browser. Should the user receive results by email too?
- [ ] **Lead persistence** — email + tier currently not stored (client-side only). Flask backend saves to `leads.csv`. Deploy backend to capture leads.
- [ ] **CORS proxy reliability** — `corsproxy.io` is a free public service. Replace with own Cloudflare Worker or deploy Flask backend.
- [ ] **API key exposure** — key is in client-side JS (visible in page source). Acceptable for internal presales use; replace with backend proxy for public-facing tool.
- [ ] **Competitor scoring** — competitor URLs are collected but not yet scored in the MVP. Backend has the plumbing ready.
- [ ] **Email collection backend** — for live landing page: integrate Formspree / Mailchimp / HubSpot form to capture leads server-side.
- [ ] **Design: results page** — consider adding a radar-style chart (Chart.js) across 5 dimensions.
- [ ] **Connect to full DMT** — after Tier II–III result, upsell path to paid ePACE Digital Maturity Assessment.
- [ ] **Move to epace.cz** — when ready to go public, host landing page under epace.cz domain.

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
| API key exposure | Server-side (.env) | Client-side JS (MVP) |

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
    └── dmt-landing-page.html   ← landing page with DMT Express form
```
