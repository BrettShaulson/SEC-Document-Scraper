"""
backend/app.py
Flask app for Google Cloud Run – SEC section scraper
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, abort
from google.cloud import datastore
from sec_api import ExtractorApi

# ---------------------------------------------------------------------------
#  ❱❱ 1.  CONFIGURATION
# ---------------------------------------------------------------------------

API_KEY = "100e904356e228588470074d0064d0faba2863b645688f30e0599f5fe5e9b602"  # ← hard-coded per your request
PROJECT_ID = "sentiment-analysis-379200"            # Datastore project
EXTRACTOR = ExtractorApi(API_KEY)
DS_CLIENT = datastore.Client(project=PROJECT_ID)

# Logging is automatically shipped to Cloud Logging in Cloud Run.
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  ❱❱ 2.  FLASK APP & ROUTES
# ---------------------------------------------------------------------------

app = Flask(__name__)

@app.route("/healthz")
@app.route("/health")
def healthz():
    """Light-weight health probe for Cloud Run."""
    return "ok", 200


@app.route("/scrape", methods=["POST"])
def scrape():
    """
    Body JSON:
      {
        "filing_url": "https://www.sec.gov/Archives/edgar/data/...",
        "sections": ["1", "7"]      # list of section IDs as strings
      }
    Returns:
      { "stored": ["1", "7"], "errors": [] }
    """
    body = request.get_json(silent=True)
    if not body or "filing_url" not in body or "sections" not in body:
        abort(400, "JSON must contain filing_url and sections")

    filing_url: str = body["filing_url"]
    sections: list[str] = body["sections"]
    stored, errors = [], []

    for sec_id in sections:
        try:
            text = EXTRACTOR.get_section(filing_url, sec_id)
            _save_section_entity(filing_url, sec_id, text)
            stored.append(sec_id)
            log.info("Stored section %s from %s", sec_id, filing_url)
        except Exception as exc:                   # noqa: BLE001
            log.exception("failed to fetch section %s: %s", sec_id, exc)
            errors.append({"id": sec_id, "msg": str(exc)})

    return jsonify({"stored": stored, "errors": errors}), 200


# ---------------------------------------------------------------------------
#  ❱❱ 3.  HELPERS
# ---------------------------------------------------------------------------

def _save_section_entity(filing_url: str, sec_id: str, text: str) -> None:
    """Persist one FilingSection entity into Datastore."""
    key = DS_CLIENT.key("FilingSection")
    entity = datastore.Entity(key=key)
    entity.update(
        filing_url=filing_url,
        section_id=sec_id,
        content=text,
        created=datetime.utcnow(),
    )
    DS_CLIENT.put(entity)


# ---------------------------------------------------------------------------
#  ❱❱ 4.  ROUTE-MAP DEBUG (prints once at container start)
# ---------------------------------------------------------------------------

if os.environ.get("PRINT_ROUTES_ON_START", "1") == "1":
    log.info("ROUTES: %s", app.url_map)

# Gunicorn will import app:app, nothing to run under __main__
