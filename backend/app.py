# SEC Document Scraper Backend
# A Flask web application that extracts sections from SEC filings and stores them in Firestore
# Author: AI Assistant
# Last Updated: 2025-07-27

# Import required libraries
from flask import Flask, request, jsonify  # Web framework for creating REST API
from flask_cors import CORS                # Cross-Origin Resource Sharing for frontend-backend communication
from sec_api import ExtractorApi          # SEC API library for extracting document sections
import re                                 # Regular expressions for pattern matching in URLs
import hashlib                            # For generating unique filing IDs
import datetime                           # For timestamps

# Configuration constants
# SEC API key for accessing sec-api.io service (provided for demo purposes)
SEC_API_KEY = "100e904356e228588470074d0064d0faba2863b645688f30e0599f5fe5e9b602"

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
SECTIONS = {
    # 10-K filings: Annual comprehensive business reports
    "10-K": ["1", "1A", "1B", "2", "3", "4", "5", "7", "7A", "8", "9", "9A", "9B", "10", "11", "12", "13", "14", "15"],
    
    # 10-Q filings: Quarterly financial reports  
    "10-Q": ["part1item1", "part1item2", "part1item3", "part1item4", "part2item1", "part2item1a", "part2item2", "part2item5", "part2item6"],
    
    # 8-K filings: Current reports for significant corporate events
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

def save_to_firestore(filing_url, filing_type, sections_data):
    """
    Save a complete SEC filing and its sections to our Firestore database.
    
    This function implements a hierarchical storage structure:
    - Main filing document with metadata
    - Sub-collection of sections with full content
    
    Args:
        filing_url (str): The original SEC URL
        filing_type (str): Type of filing (10-K, 10-Q, 8-K)
        sections_data (list): List of section dictionaries with content
        
    Returns:
        bool: True if saved successfully, False otherwise
        
    Database Structure Created:
        filings/{filing_id}/
        ├── url, filing_type, scraped_at, etc.
        └── sections/{section_id}/
            ├── content (full text)
            ├── content_length
            ├── success status
            └── timestamps
    """
    # Check if Firestore is available (might not be in local development)
    if not FIRESTORE_AVAILABLE or not db:
        print("⚠️  Firestore not available - data not saved")
        return False
    
    try:
        # Generate consistent filing ID and timestamp
        filing_id = generate_filing_id(filing_url)
        timestamp = datetime.datetime.utcnow()
        
        # Create the main filing document in the 'filings' collection
        filing_ref = db.collection('filings').document(filing_id)
        filing_data = {
            'url': filing_url,                    # Original SEC URL
            'filing_type': filing_type,           # 10-K, 10-Q, or 8-K
            'scraped_at': timestamp,              # When we processed this filing
            'sections_count': len(sections_data), # Total sections attempted
            'successful_sections': sum(1 for s in sections_data if s['success']),  # How many worked
            'failed_sections': sum(1 for s in sections_data if not s['success'])   # How many failed
        }
        # Save the main filing document
        filing_ref.set(filing_data)
        
        # Create a sub-collection for storing individual sections
        sections_ref = filing_ref.collection('sections')
        
        # Use Firestore batch writes for efficiency (all sections saved together)
        batch = db.batch()
        for section in sections_data:
            # Each section gets its own document (e.g., "1", "1A", "7")
            section_doc_ref = sections_ref.document(section['section'])
            section_data = {
                'section_id': section['section'],           # e.g., "1A"
                'content': section.get('content', ''),      # Full section text content
                'content_length': section.get('content_length', 0),  # Character count
                'success': section['success'],              # Whether extraction worked
                'error': section.get('error', ''),          # Error message if failed
                'scraped_at': timestamp                     # When this section was processed
            }
            # Add this section to the batch
            batch.set(section_doc_ref, section_data)
        
        # Execute all section saves at once for data consistency
        batch.commit()
        
        print(f"✅ Saved filing {filing_id} with {len(sections_data)} sections to Firestore (sec-documents)")
        return True
        
    except Exception as e:
        # Log any errors but don't crash the application
        print(f"❌ Failed to save to Firestore: {e}")
        return False

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
        "project_id": PROJECT_ID                   # Which Google Cloud project
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
    
    This is the core functionality of our application.
    
    Expected POST body:
        {
            "filing_url": "https://www.sec.gov/Archives/edgar/data/...",
            "sections": ["1", "1A", "7"]
        }
        
    Returns:
        {
            "filing_type": "10-K",
            "filing_id": "703e2d880500",
            "firestore_saved": true,
            "summary": {"successful_sections": 2, "failed_sections": 1, "total_sections": 3},
            "results": [...]  // Truncated content for display
        }
        
    Process:
    1. Validate input data
    2. Extract content using SEC API
    3. Store FULL content in Firestore
    4. Return truncated content for display
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
    
    # Process each requested section
    for section_id in sections:
        try:
            # Call SEC API to extract this section's content
            content = extractor.get_section(url, section_id, "text")
            
            if content and content.strip():
                # SUCCESS: We got content for this section
                
                # Full data for Firestore storage (complete content preserved)
                full_section_data = {
                    "section": section_id,
                    "success": True,
                    "content_length": len(content),
                    "content": content  # CRITICAL: Store complete content in database
                }
                results_for_storage.append(full_section_data)
                
                # Truncated data for API response (for performance)
                display_section_data = {
                    "section": section_id,
                    "success": True,
                    "content_length": len(content),
                    "content": content[:500] + "..." if len(content) > 500 else content
                }
                results_for_display.append(display_section_data)
                successful += 1
                
            else:
                # FAILURE: No content found for this section
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
            error_data = {
                "section": section_id,
                "success": False,
                "error": str(e)
            }
            results_for_storage.append(error_data)
            results_for_display.append(error_data)
            failed += 1
    
    # Save the COMPLETE content to Firestore for permanent storage
    firestore_saved = save_to_firestore(url, filing_type, results_for_storage)
    
    # Return response with truncated content for frontend display
    return jsonify({
        "filing_type": filing_type,                                    # What type we detected
        "filing_id": generate_filing_id(url) if firestore_saved else None,  # Database ID
        "firestore_saved": firestore_saved,                           # Did database save work?
        "summary": {
            "successful_sections": successful,
            "failed_sections": failed,
            "total_sections": len(sections)
        },
        "results": results_for_display  # Truncated content for UI performance
    })

@app.route('/filings')
def get_filings():
    """
    Retrieve a list of all saved filings from Firestore.
    
    Returns:
        JSON with list of filings and their metadata
        
    Use this to:
    - Browse previously scraped documents
    - See filing statistics and timestamps
    - Build a document management interface
    """
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        # Query the 'filings' collection, ordered by most recent first
        filings_ref = db.collection('filings')
        query = filings_ref.order_by('scraped_at', direction=firestore.Query.DESCENDING).limit(20)
        filings = query.stream()
        
        result = []
        for filing in filings:
            filing_data = filing.to_dict()
            result.append({
                'filing_id': filing.id,                              # Database document ID
                'url': filing_data.get('url', ''),                   # Original SEC URL
                'filing_type': filing_data.get('filing_type', ''),   # 10-K, 10-Q, 8-K
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
    """
    Retrieve the complete content of a specific section from Firestore.
    
    Args:
        filing_id (str): The unique filing identifier
        section_id (str): The section identifier (e.g., "1A", "7")
        
    Returns:
        JSON with complete section content and metadata
        
    Use this to:
    - Access the full content that was stored in the database
    - Retrieve content that was truncated in the original scrape response
    - Build detailed document viewing interfaces
    """
    if not FIRESTORE_AVAILABLE or not db:
        return jsonify({"error": "Firestore not available"}), 503
    
    try:
        # Navigate to the specific section document in the sub-collection
        filing_ref = db.collection('filings').document(filing_id)
        section_ref = filing_ref.collection('sections').document(section_id)
        section = section_ref.get()
        
        # Check if the section exists
        if not section.exists:
            return jsonify({"error": "Section not found"}), 404
        
        section_data = section.to_dict()
        
        # Also get the parent filing metadata for context
        filing = filing_ref.get()
        filing_data = filing.to_dict() if filing.exists else {}
        
        return jsonify({
            "filing_id": filing_id,
            "section_id": section_data.get('section_id'),
            "filing_type": filing_data.get('filing_type'),
            "filing_url": filing_data.get('url'),
            "content": section_data.get('content', ''),          # FULL content from database
            "content_length": section_data.get('content_length', 0),
            "success": section_data.get('success', False),
            "error": section_data.get('error', ''),
            "scraped_at": section_data.get('scraped_at').isoformat() if section_data.get('scraped_at') else None
        })
        
    except Exception as e:
        print(f"❌ Failed to fetch section: {e}")
        return jsonify({"error": f"Failed to fetch section: {e}"}), 500

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
