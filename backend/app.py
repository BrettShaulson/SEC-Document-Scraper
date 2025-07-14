"""
SEC Scraper – Flask entry-point
────────────────────────────────────────────────────────────────
• /scrape   – POST JSON {filing_url, sections[]} → stores sections in Datastore
• /healthz  – simple 200 "ok" used by Cloud Run and curl checks
"""

import datetime
import logging
from flask import Flask, request, jsonify
from google.cloud import datastore
from sec_api import ExtractorApi

# ── Config ───────────────────────────────────────────────────
SEC_API_KEY = "100e904356e228588470074d0064d0faba2863b645688f30e0599f5fe5e9b602"

logging.basicConfig(level=logging.INFO)                       # Cloud Logging
app = Flask(__name__)
extractor = ExtractorApi(SEC_API_KEY)
ds = datastore.Client()

# ── Helpers ──────────────────────────────────────────────────
def save_section(filing_url: str, section_id: str, content: str) -> None:
    """Persist a single section in Cloud Datastore (Kind: FilingSection)."""
    key = ds.key("FilingSection", f"{section_id}:{hash(filing_url)}")
    entity = datastore.Entity(key)
    entity.update(
        {
            "filing_url": filing_url,
            "section_id": section_id,
            "content": content,
            "scraped_at": datetime.datetime.utcnow(),
        }
    )
    ds.put(entity)

# ── Routes ───────────────────────────────────────────────────
@app.route("/scrape", methods=["POST"])
def scrape():
    """Scrape selected sections and store them."""
    try:
        body = request.get_json(force=True)
        filing_url = body["filing_url"]
        sections   = body["sections"]
    except Exception as err:
        return jsonify(error=f"bad request: {err}"), 400

    results = {}
    for sec_id in sections:
        try:
            text = extractor.get_section(filing_url, sec_id, "text")
            save_section(filing_url, sec_id, text)
            results[sec_id] = "stored"
        except Exception as err:
            app.logger.exception("section %s failed", sec_id)
            results[sec_id] = f"error: {err}"

    return jsonify(results), 200

# ── Health check ─────────────────────────────────────────────
@app.route("/healthz")
@app.route("/health")          # shorter alias (optional)
def healthz():
    return "ok", 200
