"""
Claude Sonnet scorer for DMT Auto.
Takes tech scan results + 5 user answers → returns Tier I–IV result JSON.
"""

import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, MODEL

QUESTIONS = [
    "Marketingová databáze",
    "Email marketing a automatizace",
    "Personalizace",
    "Zákaznická data — propojení a objem",
    "Emailová automatizace a metriky",
]

TIER_DESCRIPTIONS = {
    "I":  "Digital Infant — základní online přítomnost, data se téměř nesebírají, komunikace ad hoc.",
    "II": "Digital Aware — nástroje existují, ale jsou odpojené nebo nevyužité. Email funguje, personalizace minimální.",
    "III":"Digital Active — propojený stack, základní automatizace, data se sbírají systematicky.",
    "IV": "Digital Mature / Leader — personalizace ve škále, omnichannel, data jako základ rozhodování.",
}


def _build_tech_summary(tech: dict) -> str:
    tools = tech.get("detected_tools", [])
    lines = []
    if tools:
        lines.append(f"Detected tools: {', '.join(tools)}")
    else:
        lines.append("Detected tools: none found")

    flags = {
        "has_newsletter_form": "Newsletter signup form present",
        "has_cookie_banner_visible": "Cookie banner / CMP present",
        "has_mobile_app_links": "Mobile app links (App Store / Play Store) found",
        "has_loyalty_program": "Loyalty program or club mentioned",
        "has_exit_intent": "Exit-intent popup detected",
        "has_cart": "Shopping cart present (e-commerce)",
    }
    for key, label in flags.items():
        if tech.get(key):
            lines.append(f"✓ {label}")

    if tech.get("error"):
        lines.append(f"⚠ Scan error: {tech['error']}")
    elif not tech.get("reachable"):
        lines.append("⚠ URL was not reachable")

    return "\n".join(lines)


def _build_answers_block(answers: list[str]) -> str:
    parts = []
    for i, (q, a) in enumerate(zip(QUESTIONS, answers), 1):
        parts.append(f"Q{i} — {q}:\n{a.strip() if a.strip() else '(no answer provided)'}")
    return "\n\n".join(parts)


SCORE_PROMPT = """\
You are a senior data-driven marketing consultant at ePACE.
Your task: evaluate a company's digital marketing maturity based on two inputs:
1. Automated tech stack scan of their website (factual, no inference beyond what was detected)
2. Five free-text answers from the company representative

The scan covers what is visible in HTML source (ESP tools, analytics, CMP, reco engines, ad pixels).
The answers fill in what the scan cannot see:
  Q1: database size & collection method → Consent & Capture chapter signal
  Q2: email automation scope (welcome, flows) → Email & Communication chapter
  Q3: personalization of content/offers → Web Personalization chapter
  Q4: data unification — is customer data in one system or siloed? → CDP readiness signal
  Q5: email behavioral triggers & metrics (open rate, abandoned cart, win-back) → Timing chapter

Assign ONE tier:
  Tier I  (0–25):  Digital Infant  — minimal tech, no systematic data collection, manual comms
  Tier II  (26–50): Digital Aware   — tools exist but disconnected; email works, no real automation
  Tier III (51–75): Digital Active  — connected stack, basic automation, systematic data collection
  Tier IV (76–100): Digital Mature  — personalization at scale, omnichannel, data-driven decisions

URL: {url}

=== TECH STACK SCAN ===
{tech_summary}

=== USER ANSWERS ===
{answers_block}

Respond ONLY with a valid JSON object — no prose, no markdown fences:
{{
  "tier": "II",
  "tier_label": "Digital Aware",
  "tier_number": 2,
  "score_estimate": 38,
  "headline_cs": "One sentence in Czech summarizing the maturity level",
  "strengths_cs": ["strength 1 in Czech", "strength 2 in Czech"],
  "gaps_cs": ["gap 1 in Czech", "gap 2 in Czech"],
  "next_step_cs": "Recommended next step in Czech — 1–2 sentences",
  "reasoning_en": "2–3 sentence internal reasoning explaining the tier assignment"
}}

Rules:
- Be calibrated. Tier IV is rare. Most Czech mid-market companies land at II or III.
- Do NOT mention CDP unless the company already has one or explicitly asked about it.
- Strengths and gaps must be grounded in the scan or answers — no hallucination.
- Keep Czech texts concise (under 120 chars per item).
"""


def score_tier(url: str, tech: dict, answers: list[str]) -> dict:
    """
    Call Claude Sonnet API and return parsed tier result.
    Raises on API error or unparseable response.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = SCORE_PROMPT.format(
        url=url,
        tech_summary=_build_tech_summary(tech),
        answers_block=_build_answers_block(answers),
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a senior MarTech consultant. "
            "Respond ONLY with valid JSON — no prose, no markdown code fences."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown fences if model added them anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last resort: extract the first {...} block
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise ValueError(f"Claude returned non-JSON response: {raw[:300]}")
