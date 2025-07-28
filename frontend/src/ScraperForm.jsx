/**
 * SEC Document Scraper Frontend
 * A React component that provides a user interface for scraping SEC document sections
 * 
 * Features:
 * - Dynamic section selection based on filing type
 * - Auto-detection of filing type from URL
 * - Real-time feedback on scraping progress
 * - Integration with Flask backend API
 * 
 * Author: Brett Shaulson
 * Last Updated: 2025-07-27
 */

import React, { useState, useEffect } from "react";
import axios from "axios";  // HTTP client for making API requests
import "./ScraperForm.css";

/**
 * Determine the correct API base URL based on environment
 * 
 * Logic:
 * - Development (localhost): Use relative URLs because package.json has proxy configured
 * - Production (Google Cloud): Use same hostname with port 8080
 * 
 * This ensures the frontend can connect to the backend in both development and production
 */
const API_BASE = window.location.hostname === 'localhost' 
  ? ''  // Development: Use relative URLs because of proxy in package.json
  : `http://${window.location.hostname}:8080`;  // Production: Same IP, port 8080

/**
 * Main component for the SEC Document Scraper interface
 * 
 * This component manages:
 * - User input (URL and section selections)
 * - Communication with backend API
 * - Display of results and error states
 * - Auto-detection of filing types
 */
export default function ScraperForm() { 
  // ================================
  // STATE MANAGEMENT
  // ================================
  
  // Form input states
  const [url, setUrl] = useState("");                    // SEC document URL entered by user
  const [filingType, setFilingType] = useState("10-K");  // Currently selected filing type (10-K, 10-Q, 8-K)
  const [selectedSections, setSelectedSections] = useState({});  // Which sections user has checked
  
  // Data from backend
  const [sections, setSections] = useState({});          // Available sections for each filing type
  
  // UI states
  const [loading, setLoading] = useState(false);         // Is a scrape operation in progress?
  const [results, setResults] = useState(null);          // Results from last scrape operation
  const [error, setError] = useState("");               // Error message to display to user

  // ================================
  // EFFECT HOOKS (Side Effects)
  // ================================

  /**
   * Load available sections from backend when component mounts
   * 
   * This runs once when the component first loads and fetches the mapping
   * of filing types to their available sections (e.g., 10-K has sections 1, 1A, etc.)
   */
  useEffect(() => {
    const loadSections = async () => {
      try {
        const response = await axios.get(`${API_BASE}/sections`);
        setSections(response.data);
      } catch (err) {
        setError("Failed to load sections");
      }
    };
    loadSections();
  }, []); // Empty dependency array means this runs only once on mount

  /**
   * Auto-detect filing type whenever the URL changes
   * 
   * This provides a better user experience by automatically switching
   * to the correct filing type when a user pastes a SEC URL
   */
  useEffect(() => {
    if (url) {
      const detectType = async () => {
        try {
          const response = await axios.post(`${API_BASE}/detect-filing-type`, { url });
          setFilingType(response.data.filing_type);
          setSelectedSections({}); // Clear previous selections when type changes
        } catch (err) {
          // Silent fail - auto-detection is a convenience feature
          // If it fails, user can still manually select the filing type
        }
      };
      detectType();
    }
  }, [url]); // Runs whenever the URL state changes

  // ================================
  // EVENT HANDLERS
  // ================================

  /**
   * Toggle a section's selected state (check/uncheck)
   * 
   * @param {string} section - The section ID to toggle (e.g., "1A", "7")
   */
  const toggleSection = (section) => {
    setSelectedSections(prev => ({
      ...prev,
      [section]: !prev[section]  // Flip the boolean value for this section
    }));
  };

  /**
   * Select all available sections for the current filing type
   * 
   * Convenience function for users who want to scrape everything
   */
  const selectAllSections = () => {
    if (sections[filingType]) {
      const allSelected = {};
      // Create an object with all sections set to true
      sections[filingType].forEach(section => {
        allSelected[section] = true;
      });
      setSelectedSections(allSelected);
    }
  };

  /**
   * Clear all section selections
   * 
   * Convenience function to quickly deselect everything
   */
  const clearAllSections = () => {
    setSelectedSections({});
  };

  /**
   * Handle form submission - the main scraping operation
   * 
   * This function:
   * 1. Validates user input
   * 2. Sends scrape request to backend
   * 3. Handles success/error responses
   * 4. Updates UI with results
   * 
   * @param {Event} e - Form submission event
   */
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent browser's default form submission
    
    // Clear previous state
    setError("");
    setResults(null);

    // Get list of selected sections (only the ones that are checked)
    const selectedList = Object.keys(selectedSections).filter(key => selectedSections[key]);
    
    // Input validation
    if (!url.trim()) {
      setError("Please enter a SEC document URL");
      return;
    }
    
    if (selectedList.length === 0) {
      setError("Please select at least one section");
      return;
    }

    // Start loading state (shows spinner/disables button)
    setLoading(true);

    try {
      // Make API call to backend scraper
      const response = await axios.post(`${API_BASE}/scrape`, {
        filing_url: url,
        sections: selectedList
      });
      
      // Success! Store the results for display
      setResults(response.data);
      
    } catch (err) {
      // Handle API errors (network issues, backend errors, validation failures)
      setError(err.response?.data?.error || "Failed to scrape document");
    } finally {
      // Always turn off loading state when done
      setLoading(false);
    }
  };

  // ================================
  // RENDER USER INTERFACE
  // ================================

  return (
    <div className="scraper-container">
      <div className="scraper-card">
        
        {/* Application Header */}
        <div className="scraper-header">
          <h1>SEC Document Scraper</h1>
          <p>Extract sections from SEC 10-K, 10-Q, and 8-K filings</p>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit}>
          
          {/* URL Input Field */}
          <div className="form-group">
            <label>SEC Document URL:</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.sec.gov/Archives/edgar/data/..."
              required
            />
          </div>

          {/* Filing Type Tabs */}
          <div className="filing-type-tabs">
            {["10-K", "10-Q", "8-K"].map(type => (
              <button
                key={type}
                type="button"  // Prevent form submission
                className={`tab ${filingType === type ? 'active' : ''}`}
                onClick={() => setFilingType(type)}
              >
                {type}
              </button>
            ))}
          </div>

          {/* Section Selection (only show if we have sections for this filing type) */}
          {sections[filingType] && (
            <div className="sections-container">
              
              {/* Section Selection Header with Bulk Actions */}
              <div className="sections-header">
                <h3>Select Sections:</h3>
                <div className="section-buttons">
                  <button type="button" onClick={selectAllSections} className="btn-small">
                    Select All
                  </button>
                  <button type="button" onClick={clearAllSections} className="btn-small">
                    Clear All
                  </button>
                </div>
              </div>
              
              {/* Grid of Section Checkboxes */}
              <div className="sections-grid">
                {sections[filingType].map(section => (
                  <label key={section} className="section-item">
                    <input
                      type="checkbox"
                      checked={selectedSections[section] || false}
                      onChange={() => toggleSection(section)}
                    />
                    <span>Section {section}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Error Message Display */}
          {error && <div className="error-message">{error}</div>}

          {/* Submit Button */}
          <button 
            type="submit" 
            className="submit-btn" 
            disabled={loading}  // Disable while loading to prevent multiple submissions
          >
            {loading ? "Extracting..." : "Extract Sections"}
          </button>
        </form>

        {/* Results Display (only show if we have results) */}
        {results && (
          <div className="results-section">
            <h3>Extraction Results</h3>
            
            {/* Summary Statistics */}
            <div className="summary">
              <span className="success">✓ {results.summary.successful_sections} successful</span>
              <span className="failed">✗ {results.summary.failed_sections} failed</span>
              
              {/* Show Firestore save status if data was stored */}
              {results.firestore_saved && (
                <span className="firestore-status">🔥 Saved to Firestore</span>
              )}
            </div>
            
            {/* Filing ID (shows the database identifier for this scrape) */}
            {results.filing_id && (
              <div className="filing-info">
                <strong>Filing ID:</strong> {results.filing_id}
              </div>
            )}
            
            {/* Detailed Results for Each Section */}
            <div className="results-list">
              {results.results.map((result, index) => (
                <div key={index} className={`result-item ${result.success ? 'success' : 'failed'}`}>
                  
                  {/* Section Header with Status */}
                  <div className="result-header">
                    <strong>Section {result.section}</strong>
                    {result.success ? (
                      <span className="content-length">{result.content_length} characters</span>
                    ) : (
                      <span className="error-text">{result.error}</span>
                    )}
                  </div>
                  
                  {/* Content Preview (truncated for performance) */}
                  {result.success && result.content && (
                    <div className="content-preview">{result.content}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
