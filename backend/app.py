from flask import Flask, request, jsonify
from flask_cors import CORS
from sec_api import ExtractorApi
import re
import hashlib
import datetime

# Configuration
SEC_API_KEY = "100e904356e228588470074d0064d0faba2863b645688f30e0599f5fe5e9b602"
PROJECT_ID = "sentiment-analysis-379200"

app = Flask(__name__)
CORS(app)  # Simple CORS for all origins

extractor = ExtractorApi(SEC_API_KEY)

# Initialize Firestore
try:
    from google.cloud import firestore
    db = firestore.Client(project=PROJECT_ID, database='sec-documents')
    FIRESTORE_AVAILABLE = True
    print("✅ Firestore (sec-documents database) initialized successfully")
except Exception as e:
    print(f"⚠️  Firestore not available: {e}")
    db = None
    FIRESTORE_AVAILABLE = False

# Simplified section definitions - just the essential ones
SECTIONS = {
    "10-K": ["1", "1A", "1B", "2", "3", "4", "5", "7", "7A", "8", "9", "9A", "9B", "10", "11", "12", "13", "14", "15"],
    "10-Q": ["part1item1", "part1item2", "part1item3", "part1item4", "part2item1", "part2item1a", "part2item2", "part2item5", "part2item6"],
    "8-K": ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2", "4-1", "5-1", "5-2", "7-1", "8-1", "9-1"]
}

def generate_filing_id(url):
    """Generate a unique filing ID from URL"""
    return hashlib.md5(url.encode()).hexdigest()[:12]

def save_to_firestore(filing_url, filing_type, sections_data):
    """Save filing and sections to Firestore (sec-documents database)"""
    if not FIRESTORE_AVAILABLE or not db:
        print("⚠️  Firestore not available - data not saved")
        return False
    
    try:
        filing_id = generate_filing_id(filing_url)
        timestamp = datetime.datetime.utcnow()
        
        # Create filing document in 'filings' collection
        filing_ref = db.collection('filings').document(filing_id)
        filing_data = {
            'url': filing_url,
            'filing_type': filing_type,
            'scraped_at': timestamp,
            'sections_count': len(sections_data),
            'successful_sections': sum(1 for s in sections_data if s['success']),
            'failed_sections': sum(1 for s in sections_data if not s['success'])
        }
        filing_ref.set(filing_data)
        
        # Create sections as subcollection
        sections_ref = filing_ref.collection('sections')
        
        # Save each section as a document in the subcollection
        batch = db.batch()
        for section in sections_data:
            section_doc_ref = sections_ref.document(section['section'])
            section_data = {
                'section_id': section['section'],
                'content': section.get('content', ''),
                'content_length': section.get('content_length', 0),
                'success': section['success'],
                'error': section.get('error', ''),
                'scraped_at': timestamp
            }
            batch.set(section_doc_ref, section_data)
        
        # Commit the batch
        batch.commit()
        
        print(f"✅ Saved filing {filing_id} with {len(sections_data)} sections to Firestore (sec-documents)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save to Firestore: {e}")
        return False

def detect_filing_type(url):
    """Detect filing type from URL"""
    if re.search(r'10-?k', url, re.IGNORECASE):
        return "10-K"
    elif re.search(r'10-?q', url, re.IGNORECASE):
        return "10-Q"
    elif re.search(r'8-?k', url, re.IGNORECASE):
        return "8-K"
    return "10-K"  # Default

@app.route('/healthz')
def health():
    return jsonify({
        "status": "healthy",
        "firestore_available": FIRESTORE_AVAILABLE,
        "database": "sec-documents",
        "project_id": PROJECT_ID
    })

@app.route('/sections')
def get_sections():
    return jsonify(SECTIONS)

@app.route('/detect-filing-type', methods=['POST'])
def detect_filing():
    data = request.get_json()
    url = data.get('url', '')
    filing_type = detect_filing_type(url)
    return jsonify({"filing_type": filing_type})

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    
    # Validation
    if not data or not data.get('filing_url'):
        return jsonify({"error": "Missing filing URL"}), 400
    
    url = data['filing_url']
    sections = data.get('sections', [])
    
    if not sections:
        return jsonify({"error": "No sections selected"}), 400
    
    # Validate SEC URL
    if not re.search(r'sec\.gov', url):
        return jsonify({"error": "Please provide a valid SEC.gov URL"}), 400
    
    filing_type = detect_filing_type(url)
    results_for_storage = []  # Full content for Firestore
    results_for_display = []  # Truncated content for API response
    successful = 0
    failed = 0
    
    for section_id in sections:
        try:
            content = extractor.get_section(url, section_id, "text")
            if content and content.strip():
                # Full data for storage
                full_section_data = {
                    "section": section_id,
                    "success": True,
                    "content_length": len(content),
                    "content": content  # FULL content for Firestore
                }
                results_for_storage.append(full_section_data)
                
                # Truncated data for API response
                display_section_data = {
                    "section": section_id,
                    "success": True,
                    "content_length": len(content),
                    "content": content[:500] + "..." if len(content) > 500 else content
                }
                results_for_display.append(display_section_data)
                successful += 1
            else:
                error_data = {
                    "section": section_id,
                    "success": False,
                    "error": "No content found"
                }
                results_for_storage.append(error_data)
                results_for_display.append(error_data)
                failed += 1
        except Exception as e:
            error_data = {
                "section": section_id,
                "success": False,
                "error": str(e)
            }
            results_for_storage.append(error_data)
            results_for_display.append(error_data)
            failed += 1
    
    # Save FULL content to Firestore
    firestore_saved = save_to_firestore(url, filing_type, results_for_storage)
    
    return jsonify({
        "filing_type": filing_type,
        "filing_id": generate_filing_id(url) if firestore_saved else None,
        "firestore_saved": firestore_saved,
        "summary": {
            "successful_sections": successful,
            "failed_sections": failed,
            "total_sections": len(sections)
        },
        "results": results_for_display  # Return truncated content for display
    })

@app.route('/filings')
def get_filings():
    """Get list of saved filings from Firestore (sec-documents database)"""
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        # Query all filing documents from 'filings' collection
        filings_ref = db.collection('filings')
        query = filings_ref.order_by('scraped_at', direction=firestore.Query.DESCENDING).limit(20)
        filings = query.stream()
        
        result = []
        for filing in filings:
            filing_data = filing.to_dict()
            result.append({
                'filing_id': filing.id,
                'url': filing_data.get('url', ''),
                'filing_type': filing_data.get('filing_type', ''),
                'scraped_at': filing_data.get('scraped_at').isoformat() if filing_data.get('scraped_at') else None,
                'sections_count': filing_data.get('sections_count', 0),
                'successful_sections': filing_data.get('successful_sections', 0),
                'failed_sections': filing_data.get('failed_sections', 0)
            })
        
        return jsonify({
            "filings": result,
            "total": len(result)
        })
        
    except Exception as e:
        print(f"❌ Failed to fetch filings: {e}")
        return jsonify({"error": f"Failed to fetch filings: {e}"}), 500

@app.route('/filings/<filing_id>/sections/<section_id>')
def get_section(filing_id, section_id):
    """Get specific section content from Firestore (sec-documents database)"""
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        # Get section document from subcollection
        filing_ref = db.collection('filings').document(filing_id)
        section_ref = filing_ref.collection('sections').document(section_id)
        section = section_ref.get()
        
        if not section.exists:
            return jsonify({"error": "Section not found"}), 404
        
        section_data = section.to_dict()
        
        # Also get filing metadata
        filing = filing_ref.get()
        filing_data = filing.to_dict() if filing.exists else {}
        
        return jsonify({
            "filing_id": filing_id,
            "section_id": section_data.get('section_id'),
            "filing_type": filing_data.get('filing_type'),
            "filing_url": filing_data.get('url'),
            "content": section_data.get('content', ''),
            "content_length": section_data.get('content_length', 0),
            "success": section_data.get('success', False),
            "error": section_data.get('error', ''),
            "scraped_at": section_data.get('scraped_at').isoformat() if section_data.get('scraped_at') else None
        })
        
    except Exception as e:
        print(f"❌ Failed to fetch section: {e}")
        return jsonify({"error": f"Failed to fetch section: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
