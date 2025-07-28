# SEC Document Scraper Backend
# A Flask web application that extracts sections from SEC filings and stores them in Firestore
# Author: AI Assistant
# Last Updated: 2025-07-28
# NEW: Implements scrape session hierarchy for better data organization

# Import required libraries
from flask import Flask, request, jsonify  # Web framework for creating REST API
from flask_cors import CORS                # Cross-Origin Resource Sharing for frontend-backend communication
from sec_api import ExtractorApi          # SEC API library for extracting document sections
import re                                 # Regular expressions for pattern matching in URLs
import hashlib                            # For generating unique filing IDs
import datetime                           # For timestamps
import os                                 # For environment variables

# Configuration constants
# SEC API Configuration
# Get API key from environment variable for security, fallback to hardcoded for development
SEC_API_KEY = os.getenv('SEC_API_KEY', 'cac67934753b109012616da7f70ed62370167edcad4ffa4699d5d7cc982716b6')

# Google Cloud project ID where the Firestore database is hosted
PROJECT_ID = "sentiment-analysis-379200"

# Initialize Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) to allow requests from React frontend
# This is essential for local development where frontend (port 3000) calls backend (port 8080)
CORS(app)  # Simple CORS for all origins

# Initialize SEC API extractor with our API key
# This object will be used to make requests to sec-api.io for document extraction
extractor = ExtractorApi(SEC_API_KEY)

# Initialize Google Cloud Firestore connection
# We're connecting to a specific database called 'sec-documents' for organizing our SEC data
try:
    from google.cloud import firestore
    # Create Firestore client pointing to our specific 'sec-documents' database
    db = firestore.Client(project=PROJECT_ID, database='sec-documents')
    FIRESTORE_AVAILABLE = True
    print("✅ Firestore (sec-documents database) initialized successfully")
except Exception as e:
    # If Firestore initialization fails (e.g., no authentication), continue without it
    # This allows local development without full Google Cloud setup
    print(f"⚠️  Firestore not available: {e}")
    db = None
    FIRESTORE_AVAILABLE = False

# Define which sections are available for each type of SEC filing
# This mapping helps the frontend know what sections can be extracted
# NOTE: These section IDs must match exactly what the sec-api.io API expects
SECTIONS = {
    # 10-K filings: Annual comprehensive business reports
    # Using standard section numbers that the SEC API recognizes
    "10-K": ["1", "1A", "1B", "2", "3", "4", "5", "7", "7A", "8", "9", "9A", "9B", "10", "11", "12", "13", "14", "15"],
    
    # 10-Q filings: Quarterly financial reports  
    # Using part/item format that the SEC API recognizes
    "10-Q": ["part1item1", "part1item2", "part1item3", "part1item4", "part2item1", "part2item1a", "part2item2", "part2item5", "part2item6"],
    
    # 8-K filings: Current reports for significant corporate events
    # Using item format that the SEC API recognizes
    "8-K": ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2", "4-1", "5-1", "5-2", "7-1", "8-1", "9-1"]
}

def generate_filing_id(url):
    """
    Generate a unique, consistent ID for a SEC filing based on its URL.
    
    Args:
        url (str): The SEC EDGAR URL of the filing
        
    Returns:
        str: A 12-character hash that uniquely identifies this filing
        
    Why we do this:
    - Creates consistent IDs for the same document across multiple scraping sessions
    - Uses MD5 hash of URL, truncated to 12 chars for readability
    - Prevents duplicate entries in our database
    """
    return hashlib.md5(url.encode()).hexdigest()[:12]

def generate_session_id():
    """
    Generate a unique session ID for each scrape operation.
    
    Returns:
        str: Timestamp-based session ID (e.g., "2025-07-28_12-30-45")
        
    Why we do this:
    - Each scrape operation gets its own isolated session
    - Timestamp format makes sessions human-readable
    - Prevents mixing data from different scrape operations
    """
    return datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

def save_to_firestore(filing_url, filing_type, sections_data, requested_sections):
    """
    Save a complete SEC filing and its sections using the new scrape session hierarchy.
    
    NEW STRUCTURE:
    filings/{filing_id}/
    ├── url, filing_type, total_unique_sections, latest_session_id
    └── scrape_sessions/{session_id}/
        ├── scraped_at, sections_count, successful_sections, requested_sections
        └── sections/{section_id}/
            ├── content, content_length, success, error
            └── scraped_at
    
    Args:
        filing_url (str): The original SEC URL
        filing_type (str): Type of filing (10-K, 10-Q, 8-K)
        sections_data (list): List of section dictionaries with content
        requested_sections (list): List of section IDs that were requested
        
    Returns:
        tuple: (success: bool, filing_id: str, session_id: str)
    """
    # Check if Firestore is available (might not be in local development)
    if not FIRESTORE_AVAILABLE or not db:
        print("⚠️  Firestore not available - data not saved")
        return False, None, None
    
    try:
        # Generate consistent filing ID and unique session ID
        filing_id = generate_filing_id(filing_url)
        session_id = generate_session_id()
        timestamp = datetime.datetime.utcnow()
        
        print(f"💾 Saving filing {filing_id} with session {session_id} to Firestore...")
        
        # Reference to the main filing document
        filing_ref = db.collection('filings').document(filing_id)
        
        # Check if this filing already exists to calculate total unique sections
        existing_filing = filing_ref.get()
        existing_sessions = []
        all_unique_sections = set()
        
        if existing_filing.exists:
            # Get all existing sessions to calculate unique sections
            sessions_ref = filing_ref.collection('scrape_sessions')
            existing_sessions_docs = sessions_ref.stream()
            
            for session_doc in existing_sessions_docs:
                session_data = session_doc.to_dict()
                existing_sessions.append(session_doc.id)
                # Add sections from this session to our unique set
                session_sections_ref = sessions_ref.document(session_doc.id).collection('sections')
                session_sections = session_sections_ref.stream()
                for section_doc in session_sections:
                    section_data = section_doc.to_dict()
                    if section_data.get('success', False):
                        all_unique_sections.add(section_doc.id)
        
        # Add successful sections from current session to unique set
        successful_current_sections = [s['section'] for s in sections_data if s['success']]
        all_unique_sections.update(successful_current_sections)
        
        # Create or update the main filing document
        filing_data = {
            'url': filing_url,
            'filing_type': filing_type,
            'latest_session_id': session_id,
            'latest_scrape_at': timestamp,
            'total_unique_sections': len(all_unique_sections),
            'total_sessions': len(existing_sessions) + 1
        }
        
        # Add first_scraped_at only if this is a new filing
        if not existing_filing.exists:
            filing_data['first_scraped_at'] = timestamp
        
        filing_ref.set(filing_data, merge=True)  # Merge to preserve existing data
        print(f"✅ Updated main filing document (session {len(existing_sessions) + 1})")
        
        # Create the scrape session document
        session_ref = filing_ref.collection('scrape_sessions').document(session_id)
        session_data = {
            'scraped_at': timestamp,
            'sections_count': len(sections_data),
            'successful_sections': sum(1 for s in sections_data if s['success']),
            'failed_sections': sum(1 for s in sections_data if not s['success']),
            'requested_sections': requested_sections,
            'filing_type': filing_type,
            'filing_url': filing_url
        }
        session_ref.set(session_data)
        print(f"✅ Created scrape session {session_id}")
        
        # Create sections sub-collection within this session
        sections_ref = session_ref.collection('sections')
        
        # Use Firestore batch writes for efficiency
        batch = db.batch()
        successful_saves = 0
        
        for section in sections_data:
            section_id = section['section']
            print(f"📄 Preparing section {section_id} for session {session_id}...")
            
            section_doc_ref = sections_ref.document(section_id)
            
            # Prepare section data
            section_data = {
                'section_id': section_id,
                'content': section.get('content', ''),
                'content_length': section.get('content_length', 0),
                'success': section['success'],
                'error': section.get('error', ''),
                'scraped_at': timestamp,
                'session_id': session_id
            }
            
            # Log what we're saving
            if section_data['success']:
                content_preview = section_data['content'][:50] + "..." if len(section_data['content']) > 50 else section_data['content']
                print(f"  └─ Section {section_id}: {section_data['content_length']} chars - '{content_preview}'")
                successful_saves += 1
            else:
                print(f"  └─ Section {section_id}: FAILED - {section_data['error']}")
            
            batch.set(section_doc_ref, section_data)
        
        # Execute all section saves at once
        print(f"🚀 Committing batch with {len(sections_data)} sections for session {session_id}...")
        batch.commit()
        
        print(f"✅ Successfully saved filing {filing_id} session {session_id} with {successful_saves} successful sections")
        return True, filing_id, session_id
        
    except Exception as e:
        print(f"❌ Failed to save to Firestore: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def detect_filing_type(url):
    """
    Automatically detect the type of SEC filing from its URL.
    
    Args:
        url (str): The SEC EDGAR URL
        
    Returns:
        str: Filing type ("10-K", "10-Q", or "8-K")
        
    How it works:
    - Uses regex patterns to search for filing type indicators in the URL
    - Handles variations like "10k", "10-k", "10K", etc.
    - Defaults to "10-K" if no pattern matches
    """
    if re.search(r'10-?k', url, re.IGNORECASE):
        return "10-K"
    elif re.search(r'10-?q', url, re.IGNORECASE):
        return "10-Q"
    elif re.search(r'8-?k', url, re.IGNORECASE):
        return "8-K"
    return "10-K"  # Default to most common filing type

def validate_section_content(content, requested_section, filing_type):
    """
    Validate that the returned content actually matches the requested section.
    
    This prevents saving duplicate content when the SEC API returns the wrong section
    or falls back to a default section when the requested section doesn't exist.
    
    Args:
        content (str): The content returned by the SEC API
        requested_section (str): The section we requested (e.g., "1A", "1B")
        filing_type (str): The type of filing ("10-K", "10-Q", "8-K")
        
    Returns:
        bool: True if content matches the requested section, False otherwise
    """
    if not content:
        return False
    
    # Convert content to uppercase for case-insensitive matching
    content_upper = content.upper()
    
    # Expected section headers based on filing type and section
    expected_headers = []
    
    if filing_type == "10-K":
        if requested_section == "1":
            expected_headers = ["ITEM 1.", "ITEM 1 ", "BUSINESS"]
        elif requested_section == "1A":
            expected_headers = ["ITEM 1A.", "ITEM 1A ", "RISK FACTORS"]
        elif requested_section == "1B":
            expected_headers = ["ITEM 1B.", "ITEM 1B ", "UNRESOLVED STAFF COMMENTS"]
        elif requested_section == "2":
            expected_headers = ["ITEM 2.", "ITEM 2 ", "PROPERTIES"]
        elif requested_section == "3":
            expected_headers = ["ITEM 3.", "ITEM 3 ", "LEGAL PROCEEDINGS"]
        elif requested_section == "7":
            expected_headers = ["ITEM 7.", "ITEM 7 ", "MANAGEMENT'S DISCUSSION"]
        elif requested_section == "7A":
            expected_headers = ["ITEM 7A.", "ITEM 7A ", "QUANTITATIVE AND QUALITATIVE"]
        else:
            # For other sections, just check if it contains the item number
            expected_headers = [f"ITEM {requested_section}.", f"ITEM {requested_section} "]
    
    elif filing_type == "10-Q":
        # 10-Q sections have different naming patterns
        if "part1item1" in requested_section.lower():
            expected_headers = ["PART I", "ITEM 1", "FINANCIAL STATEMENTS"]
        elif "part1item2" in requested_section.lower():
            expected_headers = ["ITEM 2", "MANAGEMENT'S DISCUSSION"]
        else:
            # Generic check for part/item pattern
            expected_headers = ["PART", "ITEM"]
    
    elif filing_type == "8-K":
        # 8-K sections have item patterns like "1-1", "2-1"
        item_num = requested_section.split('-')[0] if '-' in requested_section else requested_section
        expected_headers = [f"ITEM {item_num}", f"ITEM {requested_section}"]
    
    # Check if any expected header is found in the content
    if expected_headers:
        for header in expected_headers:
            if header in content_upper:
                print(f"   ✅ Content validation passed: Found '{header}' for section {requested_section}")
                return True
        
        print(f"   ❌ Content validation failed: None of {expected_headers} found for section {requested_section}")
        print(f"   📄 Content preview: {content[:200]}...")
        return False
    else:
        # If we don't have specific validation rules, assume it's valid
        print(f"   ⚠️  No validation rules for section {requested_section}, assuming valid")
        return True

# =====================================
# API ENDPOINTS (REST API Routes)
# =====================================

@app.route('/healthz')
def health():
    """
    Health check endpoint for monitoring system status.
        
    Returns:
        JSON with system status, database connectivity, and configuration
        
    Use this to:
    - Check if the backend is running
    - Verify Firestore connection
    - Confirm which database and project we're using
    """
    return jsonify({
        "status": "healthy",                        # Basic service status
        "firestore_available": FIRESTORE_AVAILABLE, # Can we connect to database?
        "database": "sec-documents",                # Which Firestore database
        "project_id": PROJECT_ID,                   # Which Google Cloud project
        "structure": "scrape_sessions"              # NEW: Indicates we use session hierarchy
    })

@app.route('/sections')
def get_sections():
    """
    Return the available sections for each filing type.
    
    Returns:
        JSON mapping of filing types to their available sections
        
    The frontend uses this to:
    - Build the section selection checkboxes
    - Know which sections are valid for each filing type
    - Populate the user interface dynamically
    """
    print(f"📋 Returning section definitions: {SECTIONS}")
    return jsonify(SECTIONS)

@app.route('/detect-filing-type', methods=['POST'])
def detect_filing():
    """
    Auto-detect filing type from a SEC URL.
    
    Expected POST body:
        {"url": "https://www.sec.gov/Archives/edgar/data/..."}
        
    Returns:
        {"filing_type": "10-K"}
        
    The frontend uses this for:
    - Automatically switching tabs when user pastes a URL
    - Showing the correct sections for the detected filing type
    - Improving user experience with smart defaults
    """
    data = request.get_json()
    url = data.get('url', '')
    filing_type = detect_filing_type(url)
    return jsonify({"filing_type": filing_type})

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Main endpoint for extracting sections from SEC filings.
    
    NOW USES SCRAPE SESSION HIERARCHY for better data organization.
    
    Expected POST body:
        {
            "filing_url": "https://www.sec.gov/Archives/edgar/data/...",
            "sections": ["1", "1A", "7"]
        }
        
    Returns:
        {
            "filing_type": "10-K",
            "filing_id": "703e2d880500",
            "session_id": "2025-07-28_12-30-45",
            "firestore_saved": true,
            "summary": {"successful_sections": 2, "failed_sections": 1, "total_sections": 3},
            "results": [...]
        }
    """
    data = request.get_json()
    
    # Input validation: Check for required fields
    if not data or not data.get('filing_url'):
        return jsonify({"error": "Missing filing URL"}), 400
    
    url = data['filing_url']
    sections = data.get('sections', [])
    
    if not sections:
        return jsonify({"error": "No sections selected"}), 400
    
    # Security: Ensure URL is from SEC.gov to prevent misuse
    if not re.search(r'sec\.gov', url):
        return jsonify({"error": "Please provide a valid SEC.gov URL"}), 400
    
    # Auto-detect what type of filing this is
    filing_type = detect_filing_type(url)
    
    # Prepare separate data structures for storage vs. display
    results_for_storage = []   # Full content goes to Firestore
    results_for_display = []   # Truncated content for API response
    successful = 0
    failed = 0
    
    print(f"🔍 Starting extraction for {len(sections)} sections from {filing_type} filing")
    
    # Process each requested section
    for section_id in sections:
        try:
            print(f"📄 Extracting section {section_id}...")
            print(f"   URL: {url}")
            print(f"   Section ID: '{section_id}'")
            print(f"   Format: text")
            
            # Call SEC API to extract this section's content
            section_content = extractor.get_section(url, section_id, "text")
            
            # Debug: Show what we got back from the API
            if section_content:
                content_sample = section_content[:200].replace('\n', ' ').replace('\r', ' ')
                print(f"   🔍 API Response Preview: '{content_sample}...'")
                print(f"   📏 Content Length: {len(section_content)} characters")
            else:
                print(f"   ❌ API returned empty/None content")
            
            if section_content and section_content.strip():
                # Validate that the returned content actually matches the requested section
                content_valid = validate_section_content(section_content, section_id, filing_type)
                
                if content_valid:
                    # SUCCESS: We got valid content for this section
                    content_length = len(section_content)
                    content_preview = section_content[:100] + "..." if len(section_content) > 100 else section_content
                    print(f"✅ Section {section_id}: {content_length} chars - VALID CONTENT - '{content_preview}'")
                    
                    # Full data for Firestore storage
                    full_section_data = {
                        "section": section_id,
                        "success": True,
                        "content_length": content_length,
                        "content": str(section_content)
                    }
                    results_for_storage.append(full_section_data)
                    
                    # Truncated data for API response
                    display_section_data = {
                        "section": section_id,
                        "success": True,
                        "content_length": content_length,
                        "content": section_content[:500] + "..." if len(section_content) > 500 else section_content
                    }
                    results_for_display.append(display_section_data)
                    successful += 1
                else:
                    # FAILURE: Content doesn't match the requested section
                    print(f"❌ Section {section_id}: Content validation failed - API returned wrong section content")
                    error_data = {
                        "section": section_id,
                        "success": False,
                        "error": f"Section {section_id} not found in this document (API returned different section)"
                    }
                    results_for_storage.append(error_data)
                    results_for_display.append(error_data)
                    failed += 1
                
            else:
                # FAILURE: No content found for this section
                print(f"❌ Section {section_id}: No content found")
                error_data = {
                    "section": section_id,
                    "success": False,
                    "error": "No content found"
                }
                results_for_storage.append(error_data)
                results_for_display.append(error_data)
                failed += 1
                
        except Exception as e:
            # FAILURE: SEC API call failed
            print(f"❌ Section {section_id}: Error - {str(e)}")
            print(f"   Exception Type: {type(e).__name__}")
            import traceback
            print(f"   Stack Trace: {traceback.format_exc()}")
            error_data = {
                "section": section_id,
                "success": False,
                "error": str(e)
            }
            results_for_storage.append(error_data)
            results_for_display.append(error_data)
            failed += 1
    
    # Save using the NEW scrape session hierarchy
    firestore_saved, filing_id, session_id = save_to_firestore(
        url, filing_type, results_for_storage, sections
    )
    
    # Return response with session information
    return jsonify({
        "filing_type": filing_type,
        "filing_id": filing_id,
        "session_id": session_id,  # NEW: Session ID for this scrape operation
        "firestore_saved": firestore_saved,
        "summary": {
            "successful_sections": successful,
            "failed_sections": failed,
            "total_sections": len(sections)
        },
        "results": results_for_display
    })

@app.route('/filings')
def get_filings():
    """
    Retrieve a list of all saved filings with their session information.
    
    Returns:
        JSON with list of filings and their metadata including latest session info
    """
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        filings_ref = db.collection('filings')
        query = filings_ref.order_by('latest_scrape_at', direction=firestore.Query.DESCENDING).limit(20)
        filings = query.stream()
        
        result = []
        for filing in filings:
            filing_data = filing.to_dict()
            result.append({
                'filing_id': filing.id,
                'url': filing_data.get('url', ''),
                'filing_type': filing_data.get('filing_type', ''),
                'first_scraped_at': filing_data.get('first_scraped_at').isoformat() if filing_data.get('first_scraped_at') else None,
                'latest_scrape_at': filing_data.get('latest_scrape_at').isoformat() if filing_data.get('latest_scrape_at') else None,
                'latest_session_id': filing_data.get('latest_session_id', ''),
                'total_unique_sections': filing_data.get('total_unique_sections', 0),
                'total_sessions': filing_data.get('total_sessions', 0)
            })
        
        return jsonify({
            "filings": result,
            "total": len(result)
        })
        
    except Exception as e:
        print(f"❌ Failed to fetch filings: {e}")
        return jsonify({"error": f"Failed to fetch filings: {e}"}), 500

@app.route('/filings/<filing_id>/sessions')
def get_filing_sessions(filing_id):
    """
    Get all scrape sessions for a specific filing.
    
    Returns:
        JSON with list of scrape sessions and their metadata
    """
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        filing_ref = db.collection('filings').document(filing_id)
        sessions_ref = filing_ref.collection('scrape_sessions')
        sessions_query = sessions_ref.order_by('scraped_at', direction=firestore.Query.DESCENDING)
        sessions = sessions_query.stream()
        
        result = []
        for session in sessions:
            session_data = session.to_dict()
            result.append({
                'session_id': session.id,
                'scraped_at': session_data.get('scraped_at').isoformat() if session_data.get('scraped_at') else None,
                'sections_count': session_data.get('sections_count', 0),
                'successful_sections': session_data.get('successful_sections', 0),
                'failed_sections': session_data.get('failed_sections', 0),
                'requested_sections': session_data.get('requested_sections', [])
            })
        
        return jsonify({
            "filing_id": filing_id,
            "sessions": result,
            "total_sessions": len(result)
        })
        
    except Exception as e:
        print(f"❌ Failed to fetch sessions: {e}")
        return jsonify({"error": f"Failed to fetch sessions: {e}"}), 500

@app.route('/filings/<filing_id>/sessions/<session_id>/sections')
def get_session_sections(filing_id, session_id):
    """
    Get all sections from a specific scrape session.
    
    Returns:
        JSON with list of sections from this session
    """
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        filing_ref = db.collection('filings').document(filing_id)
        session_ref = filing_ref.collection('scrape_sessions').document(session_id)
        sections_ref = session_ref.collection('sections')
        sections = sections_ref.stream()
        
        result = []
        for section in sections:
            section_data = section.to_dict()
            result.append({
                'section_id': section.id,
                'content_length': section_data.get('content_length', 0),
                'success': section_data.get('success', False),
                'error': section_data.get('error', ''),
                'scraped_at': section_data.get('scraped_at').isoformat() if section_data.get('scraped_at') else None
            })
        
        return jsonify({
            "filing_id": filing_id,
            "session_id": session_id,
            "sections": result,
            "total_sections": len(result)
        })
        
    except Exception as e:
        print(f"❌ Failed to fetch session sections: {e}")
        return jsonify({"error": f"Failed to fetch session sections: {e}"}), 500

@app.route('/filings/<filing_id>/sessions/<session_id>/sections/<section_id>')
def get_session_section(filing_id, session_id, section_id):
    """
    Get a specific section from a specific scrape session.
    
    Returns:
        JSON with complete section content and metadata
    """
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        # Navigate to the specific section in the session hierarchy
        filing_ref = db.collection('filings').document(filing_id)
        session_ref = filing_ref.collection('scrape_sessions').document(session_id)
        section_ref = session_ref.collection('sections').document(section_id)
        section = section_ref.get()
        
        if not section.exists:
            return jsonify({"error": "Section not found"}), 404
        
        section_data = section.to_dict()
        
        # Get session metadata for context
        session = session_ref.get()
        session_data = session.to_dict() if session.exists else {}
        
        # Get filing metadata for context
        filing = filing_ref.get()
        filing_data = filing.to_dict() if filing.exists else {}
        
        return jsonify({
            "filing_id": filing_id,
            "session_id": session_id,
            "section_id": section_data.get('section_id'),
            "filing_type": session_data.get('filing_type'),
            "filing_url": session_data.get('filing_url'),
            "content": section_data.get('content', ''),
            "content_length": section_data.get('content_length', 0),
            "success": section_data.get('success', False),
            "error": section_data.get('error', ''),
            "scraped_at": section_data.get('scraped_at').isoformat() if section_data.get('scraped_at') else None,
            "session_scraped_at": session_data.get('scraped_at').isoformat() if session_data.get('scraped_at') else None
        })
        
    except Exception as e:
        print(f"❌ Failed to fetch session section: {e}")
        return jsonify({"error": f"Failed to fetch session section: {e}"}), 500

# LEGACY ENDPOINT: Maintained for backward compatibility
@app.route('/filings/<filing_id>/sections/<section_id>')
def get_section_legacy(filing_id, section_id):
    """
    LEGACY: Get section from the latest session (for backward compatibility).
    
    This endpoint finds the most recent session and returns the section from there.
    """
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        # Find the latest session for this filing
        filing_ref = db.collection('filings').document(filing_id)
        filing = filing_ref.get()
        
        if not filing.exists:
            return jsonify({"error": "Filing not found"}), 404
        
        filing_data = filing.to_dict()
        latest_session_id = filing_data.get('latest_session_id')
        
        if not latest_session_id:
            return jsonify({"error": "No sessions found for this filing"}), 404
        
        # Redirect to the new session-based endpoint
        return get_session_section(filing_id, latest_session_id, section_id)
        
    except Exception as e:
        print(f"❌ Failed to fetch legacy section: {e}")
        return jsonify({"error": f"Failed to fetch section: {e}"}), 500

@app.route('/debug/test-section', methods=['POST'])
def debug_test_section():
    """
    Debug endpoint to test SEC API extraction for a specific section.
    
    Expected POST body:
        {
            "filing_url": "https://www.sec.gov/Archives/edgar/data/...",
            "section": "1A"
        }
        
    Returns detailed information about what the SEC API returns for this specific section.
    """
    data = request.get_json()
    
    if not data or not data.get('filing_url') or not data.get('section'):
        return jsonify({"error": "Missing filing_url or section"}), 400
    
    url = data['filing_url']
    section_id = data['section']
    
    print(f"🧪 DEBUG: Testing section extraction")
    print(f"   URL: {url}")
    print(f"   Section: {section_id}")
    
    try:
        # Test the SEC API call
        content = extractor.get_section(url, section_id, "text")
        
        result = {
            "section_id": section_id,
            "url": url,
            "content_found": content is not None,
            "content_length": len(content) if content else 0,
            "content_preview": content[:500] if content else None,
            "content_first_100_chars": content[:100] if content else None
        }
        
        print(f"🧪 DEBUG Result: {result}")
        return jsonify(result)
        
    except Exception as e:
        error_result = {
            "section_id": section_id,
            "url": url,
            "error": str(e),
            "error_type": type(e).__name__
        }
        print(f"🧪 DEBUG Error: {error_result}")
        return jsonify(error_result), 500

# =====================================
# APPLICATION STARTUP
# =====================================

if __name__ == '__main__':
    """
    Start the Flask development server.
    
    Configuration:
    - host='0.0.0.0': Accept connections from any IP (allows frontend to connect)
    - port=8080: Use port 8080 (standard for backend services)
    - debug=False: Run in production mode for stability
    
    The server will start and listen for requests from the React frontend.
    """
    app.run(host='0.0.0.0', port=8080, debug=False)
