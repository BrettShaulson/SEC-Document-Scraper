"""
backend/app.py
────────────────────────────────────────────────────────
Flask + Gunicorn entry-point for the SEC-scraper Cloud Run service
"""

import datetime
import logging
from flask import Flask, request, jsonify
from google.cloud import datastore
from sec_api import ExtractorApi

# ── Config ────────────────────────────────────────────────────────────────────
SEC_API_KEY = "100e904356e228588470074d0064d0faba2863b645688f30e0599f5fe5e9b602"

logging.basicConfig(level=logging.INFO)         # Cloud Logging picks this up
app = Flask(__name__)
extractor = ExtractorApi(SEC_API_KEY)
ds = datastore.Client()

# ── Helpers ───────────────────────────────────────────────────────────────────
def save_section(filing_url: str, section_id: str, content: str) -> None:
    """
    Persist the scraped section in Cloud Datastore.

    Kind: FilingSection
    Key : <section_id>:<hash(filing_url)>
    """
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

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/scrape", methods=["POST"])
def scrape():
    """
    Body JSON:
      {
        "filing_url": "https://www.sec.gov/Archives/…10k.htm",
        "sections":   ["1", "7"]
      }
    """
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
            app.logger.exception(f"section {sec_id} failed")
            results[sec_id] = f"error: {err}"

    return jsonify(results), 200

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/healthz")
@app.route("/health")               # optional shorter path
def healthz():
    """
    Cloud Run uses this for container health-checks.
    Returns 200 OK with plain-text 'ok'.
    """
    return "ok", 200
