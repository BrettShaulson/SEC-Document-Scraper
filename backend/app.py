import datetime, logging, os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sec_api import ExtractorApi
import re

# Configuration
SEC_API_KEY = "100e904356e228588470074d0064d0faba2863b645688f30e0599f5fe5e9b602"
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
PORT = int(os.environ.get('PORT', 8080))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

app = Flask(__name__)

# Configure CORS for production
if os.environ.get('FLASK_ENV') == 'production':
    # In production, only allow specific origins
    allowed_origins = [
        'https://your-frontend-domain.com',  # Replace with actual frontend domain
        'http://localhost:3000'  # For local development
    ]
    CORS(app, origins=allowed_origins)
else:
    # In development, allow all origins
    CORS(app)

extractor = ExtractorApi(SEC_API_KEY)

# Initialize Google Cloud Datastore
try:
    from google.cloud import datastore
    if PROJECT_ID:
        ds = datastore.Client(project=PROJECT_ID)
    else:
        ds = datastore.Client()
    DATASTORE_AVAILABLE = True
    app.logger.info("Google Cloud Datastore initialized successfully")
except Exception as e:
    app.logger.error(f"Failed to initialize Google Cloud Datastore: {e}")
    ds = None
    DATASTORE_AVAILABLE = False

# Comprehensive section definitions
SECTION_DEFINITIONS = {
    "10-K": {
        "1": "Business - Description of business operations, products, services, and industry",
        "1A": "Risk Factors - Material risks that could affect business, financial condition, or results",
        "1B": "Unresolved Staff Comments - SEC staff comments on previous filings",
        "1C": "Cybersecurity - Material cybersecurity risks, incidents, and governance",
        "2": "Properties - Description of physical properties owned or leased",
        "3": "Legal Proceedings - Material pending legal proceedings",
        "4": "Mine Safety Disclosures - Safety information for mining companies",
        "5": "Market for Registrant's Common Equity - Stock performance and dividend info",
        "6": "Reserved - (Not used in current filings)",
        "7": "Management's Discussion and Analysis - MD&A of financial condition and results",
        "7A": "Quantitative and Qualitative Disclosures About Market Risk",
        "8": "Financial Statements and Supplementary Data - Audited financial statements",
        "9": "Changes in and Disagreements with Accountants - Auditor changes and disputes",
        "9A": "Controls and Procedures - Internal control assessment and certifications",
        "9B": "Other Information - Additional material information",
        "9C": "Disclosure Regarding Foreign Jurisdictions - For foreign private issuers",
        "10": "Directors, Executive Officers and Corporate Governance",
        "11": "Executive Compensation - Compensation discussion and analysis",
        "12": "Security Ownership - Principal stockholder and management ownership",
        "13": "Certain Relationships and Related Transactions - Related party transactions",
        "14": "Principal Accountant Fees and Services - Auditor fee disclosures",
        "15": "Exhibits and Financial Statement Schedules - Index of exhibits and schedules"
    },
    "10-Q": {
        "part1item1": "Financial Statements (Part 1) - Condensed financial statements",
        "part1item2": "Management's Discussion and Analysis (Part 1) - MD&A",
        "part1item3": "Quantitative and Qualitative Disclosures About Market Risk (Part 1)",
        "part1item4": "Controls and Procedures (Part 1) - Internal control assessment",
        "part2item1": "Legal Proceedings (Part 2) - Material pending legal proceedings",
        "part2item1a": "Risk Factors (Part 2) - Material risk factors",
        "part2item2": "Unregistered Sales of Equity Securities (Part 2) - Share repurchases",
        "part2item3": "Defaults Upon Senior Securities (Part 2)",
        "part2item4": "Mine Safety Disclosures (Part 2) - For mining companies",
        "part2item5": "Other Information (Part 2) - Additional material information",
        "part2item6": "Exhibits (Part 2) - Index of exhibits"
    },
    "8-K": {
        "1-1": "Entry into a Material Definitive Agreement",
        "1-2": "Completion of Acquisition or Disposition of Assets",
        "1-3": "Bankruptcy or Receivership",
        "1-4": "Mine Safety - Reporting of Shutdowns and Patterns of Violations",
        "2-1": "Completion of Acquisition or Disposition of Assets",
        "2-2": "Results of Operations and Financial Condition",
        "2-3": "Creation of a Direct Financial Obligation",
        "2-4": "Triggering Events That Accelerate or Increase a Direct Financial Obligation",
        "2-5": "Costs Associated with Exit or Disposal Activities",
        "2-6": "Material Impairments",
        "3-1": "Notice of Delisting or Failure to Satisfy Exchange Listing Standard",
        "3-2": "Unregistered Sales of Equity Securities",
        "3-3": "Material Modification to Rights of Security Holders",
        "4-1": "Changes in Registrant's Certifying Accountant",
        "4-2": "Non-Reliance on Previously Issued Financial Statements",
        "5-1": "Changes in Financial Statements or Accountants",
        "5-2": "Departure of Directors or Certain Officers",
        "5-3": "Amendment to Articles of Incorporation or Bylaws",
        "5-4": "Temporary Suspension of Trading Under Employee Benefit Plans",
        "5-5": "Amendment to Registrant's Code of Ethics",
        "5-6": "Change in Shell Company Status",
        "5-7": "Submission of Matters to a Vote of Security Holders",
        "5-8": "Shareholder Director Nominations",
        "7-1": "Regulation FD Disclosure",
        "8-1": "Other Events",
        "9-1": "Financial Statements and Exhibits",
        "signature": "Signature"
    }
}

def save_section(url: str, section_id: str, content: str, filing_type: str):
    """Save section to Google Cloud Datastore"""
    if not DATASTORE_AVAILABLE or not ds:
        app.logger.warning(f"Datastore not available - section {section_id} not saved")
        return False
    
    try:
        # Create a more comprehensive entity with additional metadata
        entity_key = ds.key("FilingSection", f"{section_id}:{hash(url)}:{datetime.datetime.utcnow().timestamp()}")
        entity = datastore.Entity(entity_key)
        entity.update({
            "filing_url": url,
            "section_id": section_id,
            "filing_type": filing_type,
            "content": content,
            "content_length": len(content) if content else 0,
            "scraped_at": datetime.datetime.utcnow(),
            "project_id": PROJECT_ID or "unknown"
        })
        
        ds.put(entity)
        app.logger.info(f"Successfully saved section {section_id} to Datastore")
        return True
        
    except Exception as e:
        app.logger.error(f"Failed to save section {section_id} to Datastore: {e}")
        return False

def detect_filing_type(url: str):
    """Detect the filing type from the URL"""
    url_lower = url.lower()
    if "10-k" in url_lower:
        return "10-K"
    elif "10-q" in url_lower:
        return "10-Q"
    elif "8-k" in url_lower:
        return "8-K"
    else:
        return "10-K"  # Default

@app.route("/", methods=["GET"])
def root():
    """Root endpoint for health checking"""
    return jsonify({
        "service": "SEC Document Section Scraper",
        "status": "running",
        "version": "1.0.0",
        "datastore_available": DATASTORE_AVAILABLE
    }), 200

@app.route("/sections", methods=["GET"])
def get_sections():
    """Return available sections for each filing type"""
    return jsonify(SECTION_DEFINITIONS), 200

@app.route("/detect-filing-type", methods=["POST"])
def detect_filing_type_endpoint():
    """Detect filing type from URL"""
    try:
        body = request.get_json(force=True)
        url = body.get("filing_url", "")
        filing_type = detect_filing_type(url)
        return jsonify({"filing_type": filing_type}), 200
    except Exception as e:
        app.logger.error(f"Error detecting filing type: {e}")
        return jsonify({"error": f"Error detecting filing type: {e}"}), 400

@app.route("/scrape", methods=["POST"])
def scrape():
    """Extract sections from SEC filing"""
    try:
        body = request.get_json(force=True)
        url = body.get("filing_url")
        secs = body.get("sections", [])
        
        if not url:
            return jsonify({"error": "filing_url is required"}), 400
        if not secs:
            return jsonify({"error": "At least one section must be selected"}), 400
        
        # Validate URL format
        if not url.startswith("https://www.sec.gov/") and not url.startswith("http://www.sec.gov/"):
            return jsonify({"error": "URL must be from SEC EDGAR website"}), 400
            
    except Exception as e:
        app.logger.error(f"Invalid request format: {e}")
        return jsonify({"error": f"Invalid request format: {e}"}), 400

    filing_type = detect_filing_type(url)
    results = {}
    successful_sections = []
    failed_sections = []
    
    app.logger.info(f"Starting extraction for {len(secs)} sections from {filing_type} filing")
    
    for section in secs:
        try:
            app.logger.info(f"Extracting section {section} from {url}")
            txt = extractor.get_section(url, section, "text")
            
            # Save to Datastore
            if save_section(url, section, txt, filing_type):
                storage_msg = "Section extracted and stored successfully in Datastore"
            else:
                storage_msg = "Section extracted but Datastore storage failed"
            
            results[section] = {
                "status": "success",
                "message": storage_msg,
                "content_length": len(txt) if txt else 0
            }
            successful_sections.append(section)
            
        except Exception as err:
            app.logger.exception(f"Section {section} extraction failed: {err}")
            results[section] = {
                "status": "error",
                "message": str(err)
            }
            failed_sections.append(section)
    
    response = {
        "results": results,
        "summary": {
            "total_sections": len(secs),
            "successful": len(successful_sections),
            "failed": len(failed_sections),
            "successful_sections": successful_sections,
            "failed_sections": failed_sections,
            "filing_type": filing_type
        },
        "datastore_available": DATASTORE_AVAILABLE,
        "project_id": PROJECT_ID
    }
    
    app.logger.info(f"Extraction completed: {len(successful_sections)} successful, {len(failed_sections)} failed")
    status_code = 200 if len(successful_sections) > 0 else 400
    return jsonify(response), status_code

@app.route("/healthz", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "datastore_available": DATASTORE_AVAILABLE,
        "project_id": PROJECT_ID,
        "version": "1.0.0"
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=PORT)
