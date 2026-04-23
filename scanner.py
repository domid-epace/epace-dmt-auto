"""
Tech stack scanner for DMT Auto.
Only detects what is factually present in HTML source — no hallucination.
"""

import re
import requests
from typing import Optional


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 12

# (signal_key, human_label, regex_pattern)
SIGNALS = [
    ("gtm",           "Google Tag Manager",   r"GTM-[A-Z0-9]+|googletagmanager\.com"),
    ("ga4",           "Google Analytics 4",   r"G-[A-Z0-9]{6,}|gtag\("),
    ("meta_pixel",    "Meta Pixel",           r"fbq\(|connect\.facebook\.net/signals"),
    ("tiktok_pixel",  "TikTok Pixel",         r"analytics\.tiktok\.com"),
    ("google_ads",    "Google Ads",           r"AW-[0-9]{7,}|googleadservices\.com"),
    ("bloomreach",    "Bloomreach",           r"bloomreach|brx\.pixel|brxapi|exponea\.com|sdk\.exponea"),
    ("klaviyo",       "Klaviyo",              r"klaviyo|static\.klaviyo"),
    ("emarsys",       "Emarsys",              r"emarsys|scarab\.it"),
    ("salesforce_mc", "Salesforce MC",        r"exacttarget|salesforce\.com/marketingcloud|mc\.js"),
    ("dotdigital",    "Dotdigital",           r"dotdigital|dmtracking\.com"),
    ("mailchimp",     "Mailchimp",            r"mailchimp|list-manage\.com"),
    ("luigi_box",     "Luigi's Box",          r"luigisbox|luigi['\"]?s box|lb\.live/"),
    ("klevu",         "Klevu",                r"klevu"),
    ("nosto",         "Nosto",                r"nosto\.com"),
    ("hotjar",        "Hotjar",               r"hotjar|static\.hotjar"),
    ("ms_clarity",    "Microsoft Clarity",    r"clarity\.ms"),
    ("cookiebot",     "Cookiebot",            r"cookiebot|cookielaw\.org"),
    ("onetrust",      "OneTrust",             r"onetrust"),
    ("cookiepro",     "CookiePro",            r"cookiepro"),
    ("usercentrics",  "Usercentrics",         r"usercentrics"),
    ("intercom",      "Intercom",             r"intercom\.io|widget\.intercom"),
    ("zendesk",       "Zendesk",              r"zendesk\.com|zd-widget"),
    ("tidio",         "Tidio",                r"tidio"),
    ("livechat",      "LiveChat",             r"livechatinc\.com|livechat_chat_window"),
    ("tawkto",        "Tawk.to",              r"tawk\.to"),
    ("segment",       "Segment",              r"segment\.io|segment\.com/analytics"),
    ("meiro",         "Meiro",                r"meiro\.io"),
    ("optimizely",    "Optimizely",           r"optimizely"),
    ("vwo",           "VWO",                  r"vwo\.com|visualwebsiteoptimizer"),
    ("service_worker","PWA / Service Worker", r"ServiceWorker|registerServiceWorker"),
]

def scan_tech_stack(url: str) -> dict:
    """
    Fetch the homepage HTML and detect tech stack signals.
    Returns a dict with boolean flags, detected tool names, and raw signals.
    Does NOT infer anything beyond what is literally present in the source.
    """
    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "error": None,
        "detected_tools": [],
        "signals": {},
        "has_newsletter_form": False,
        "has_cookie_banner_visible": False,
        "has_mobile_app_links": False,
        "has_loyalty_program": False,
        "has_exit_intent": False,
        "has_cart": False,
        "page_title": None,
    }

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        result["reachable"] = True
        result["status_code"] = resp.status_code
        html = resp.text
    except requests.RequestException as e:
        result["error"] = str(e)
        return result

    # Run all signal patterns
    for key, label, pattern in SIGNALS:
        found = bool(re.search(pattern, html, re.IGNORECASE))
        result["signals"][key] = found
        if found:
            result["detected_tools"].append(label)

    # Additional heuristics (single-line, no inference)
    result["has_newsletter_form"] = bool(
        re.search(r'newsletter|odběr|subscribe|přihlásit.*e-mail', html, re.IGNORECASE)
    )
    result["has_cookie_banner_visible"] = bool(
        re.search(
            r'cookie-banner|cookiebanner|cookies-consent|cookie_consent|cookieconsent|'
            r'cookie-notice|lišta.*cookies|souhlas.*cookies',
            html, re.IGNORECASE
        )
    ) or result["signals"].get("cookiebot") or result["signals"].get("onetrust")

    result["has_mobile_app_links"] = bool(
        re.search(r'play\.google\.com/store|apps\.apple\.com', html, re.IGNORECASE)
    )
    result["has_loyalty_program"] = bool(
        re.search(r'věrnostní|loyalty|body.*program|věrnostní.*program|klub|fidelity', html, re.IGNORECASE)
    )
    result["has_exit_intent"] = bool(
        re.search(r'exitIntent|exit[_-]intent|beforeunload|mouseleave', html, re.IGNORECASE)
    )
    result["has_cart"] = bool(
        re.search(r'košík|cart|basket|add.to.cart|addtocart', html, re.IGNORECASE)
    )

    # Page title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        result["page_title"] = title_match.group(1).strip()[:120]

    return result
