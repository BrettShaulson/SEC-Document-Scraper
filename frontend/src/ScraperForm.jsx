import React, { useState, useEffect } from "react";
import axios from "axios";
import "./ScraperForm.css";

const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8080' 
  : 'https://your-production-backend.com';

export default function ScraperForm() { 
  const [url, setUrl] = useState("");
  const [filingType, setFilingType] = useState("10-K");
  const [selectedSections, setSelectedSections] = useState({});
  const [sections, setSections] = useState({});
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");

  // Load sections on mount
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
  }, []);

  // Auto-detect filing type when URL changes
  useEffect(() => {
    if (url) {
      const detectType = async () => {
        try {
          const response = await axios.post(`${API_BASE}/detect-filing-type`, { url });
          setFilingType(response.data.filing_type);
          setSelectedSections({}); // Reset selections
        } catch (err) {
          // Silent fail for auto-detection
        }
      };
      detectType();
    }
  }, [url]);

  const toggleSection = (section) => {
    setSelectedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const selectAllSections = () => {
    if (sections[filingType]) {
      const allSelected = {};
      sections[filingType].forEach(section => {
        allSelected[section] = true;
      });
      setSelectedSections(allSelected);
    }
  };

  const clearAllSections = () => {
    setSelectedSections({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResults(null);

    const selectedList = Object.keys(selectedSections).filter(key => selectedSections[key]);
    
    if (!url.trim()) {
      setError("Please enter a SEC document URL");
      return;
    }
    
    if (selectedList.length === 0) {
      setError("Please select at least one section");
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/scrape`, {
        filing_url: url,
        sections: selectedList
      });
      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to scrape document");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scraper-container">
      <div className="scraper-card">
        <div className="scraper-header">
          <h1>SEC Document Scraper</h1>
          <p>Extract sections from SEC 10-K, 10-Q, and 8-K filings</p>
        </div>

        <form onSubmit={handleSubmit}>
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

          <div className="filing-type-tabs">
            {["10-K", "10-Q", "8-K"].map(type => (
              <button
                key={type}
                type="button"
                className={`tab ${filingType === type ? 'active' : ''}`}
                onClick={() => setFilingType(type)}
              >
                {type}
              </button>
            ))}
          </div>

          {sections[filingType] && (
            <div className="sections-container">
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

          {error && <div className="error-message">{error}</div>}

          <button 
            type="submit" 
            className="submit-btn" 
            disabled={loading}
          >
            {loading ? "Extracting..." : "Extract Sections"}
          </button>
        </form>

        {results && (
          <div className="results-section">
            <h3>Extraction Results</h3>
            <div className="summary">
              <span className="success">✓ {results.summary.successful_sections} successful</span>
              <span className="failed">✗ {results.summary.failed_sections} failed</span>
              {results.firestore_saved && (
                <span className="firestore-status">🔥 Saved to Firestore</span>
              )}
            </div>
            
            {results.filing_id && (
              <div className="filing-info">
                <strong>Filing ID:</strong> {results.filing_id}
              </div>
            )}
            
            <div className="results-list">
              {results.results.map((result, index) => (
                <div key={index} className={`result-item ${result.success ? 'success' : 'failed'}`}>
                  <div className="result-header">
                    <strong>Section {result.section}</strong>
                    {result.success ? (
                      <span className="content-length">{result.content_length} characters</span>
                    ) : (
                      <span className="error-text">{result.error}</span>
                    )}
                  </div>
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
