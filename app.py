"""
DMT Auto — lightweight Flask API backend.

Endpoints:
  POST /api/assess   — runs tech scan + Claude scoring, saves lead
  GET  /api/leads    — returns collected leads as JSON (internal use)
  GET  /health       — liveness check

Run:
  python app.py               # dev (port 5050)
  gunicorn app:app -b 0.0.0.0:5050   # production
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import LEADS_FILE
from scanner import scan_tech_stack
from scorer import score_tier

app = Flask(__name__)
CORS(app)  # allow the landing page (any origin) to call this API


# ── Helpers ────────────────────────────────────────────────────────────────────

def _save_lead(email: str, name: str, url: str, tier: str, tier_label: str) -> None:
    """Append a lead row to leads.csv (creates file + header on first run)."""
    file_exists = LEADS_FILE.exists()
    with LEADS_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "email", "name", "url", "tier", "tier_label"])
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            email, name, url, tier, tier_label,
        ])


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/assess", methods=["POST"])
def assess():
    """
    Body (JSON):
      url          str   required  — main website URL
      competitors  list  optional  — up to 2 competitor URLs (not scored, future use)
      answers      list  required  — exactly 5 free-text answer strings
      email        str   required  — lead email
      name         str   optional  — lead name
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    url = (data.get("url") or "").strip()
    answers = data.get("answers", [])
    email = (data.get("email") or "").strip()
    name = (data.get("name") or "").strip()

    if not url:
        return jsonify({"error": "url is required"}), 400
    if not email:
        return jsonify({"error": "email is required"}), 400
    if len(answers) < 5:
        return jsonify({"error": "Exactly 5 answers required"}), 400

    # Ensure URL has a scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # 1. Tech stack scan
    try:
        tech = scan_tech_stack(url)
    except Exception as e:
        tech = {"url": url, "reachable": False, "error": str(e), "detected_tools": [], "signals": {}}

    # 2. Claude scoring
    try:
        result = score_tier(url, tech, answers[:5])
    except Exception as e:
        return jsonify({"error": f"Scoring failed: {e}"}), 500

    # 3. Save lead
    try:
        _save_lead(email, name, url, result.get("tier", "?"), result.get("tier_label", "?"))
    except Exception:
        pass  # don't fail the request if CSV write fails

    # 4. Return result + tech summary to the frontend
    return jsonify({
        **result,
        "tech_detected": tech.get("detected_tools", []),
        "url_scanned": url,
    })


@app.route("/api/leads")
def leads():
    """Return all collected leads as JSON. Protect with a simple token in production."""
    token = request.args.get("token", "")
    expected = os.getenv("LEADS_TOKEN", "")
    if expected and token != expected:
        return jsonify({"error": "Unauthorized"}), 401

    if not LEADS_FILE.exists():
        return jsonify([])

    rows = []
    with LEADS_FILE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return jsonify(rows)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
