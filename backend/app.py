import datetime, logging
from flask import Flask, request, jsonify
from google.cloud import datastore
from sec_api import ExtractorApi

SEC_API_KEY = "100e904356e228588470074d0064d0faba2863b645688f30e0599f5fe5e9b602"

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
extractor = ExtractorApi(SEC_API_KEY)
ds = datastore.Client()

def save_section(url: str, section_id: str, content: str):
    key = ds.key("FilingSection", f"{section_id}:{hash(url)}")
    ent = datastore.Entity(key)
    ent.update(
        {
            "filing_url": url,
            "section_id": section_id,
            "content": content,
            "scraped_at": datetime.datetime.utcnow(),
        }
    )
    ds.put(ent)

@app.route("/scrape", methods=["POST"])
def scrape():
    try:
        body = request.get_json(force=True)
        url = body["filing_url"]
        secs = body["sections"]
    except Exception as e:
        return jsonify(error=f"bad request: {e}"), 400

    out = {}
    for s in secs:
        try:
            txt = extractor.get_section(url, s, "text")
            save_section(url, s, txt)
            out[s] = "stored"
        except Exception as err:
            app.logger.exception(f"section {s} failed")
            out[s] = f"error: {err}"
    return jsonify(out), 200

@app.route("/healthz")
def health():
    return "ok", 200
