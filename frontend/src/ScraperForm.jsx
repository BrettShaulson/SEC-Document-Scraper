import React, { useState, useEffect } from "react";
import axios from "axios";
import "./ScraperForm.css";

// API configuration for different environments
const getApiBase = () => {
  // Force localhost for development
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('🔧 Development mode detected - using localhost:8080');
    return 'http://localhost:8080';
  }
  
  // Check for explicit environment variable first
  if (process.env.REACT_APP_API_BASE) {
    console.log('🔧 Using REACT_APP_API_BASE:', process.env.REACT_APP_API_BASE);
    return process.env.REACT_APP_API_BASE;
  }
  
  // In production, try to construct from hostname
  if (process.env.NODE_ENV === 'production') {
    const hostname = window.location.hostname;
    console.log('🔧 Production mode - hostname:', hostname);
    
    if (hostname.includes('appspot.com') || hostname.includes('run.app')) {
      // Assume backend is on the same domain or a known backend domain
      const apiUrl = `https://${hostname.replace('frontend-', '')}`;
      console.log('🔧 Constructed API URL:', apiUrl);
      return apiUrl;
    }
    
    // Fallback for production
    console.log('🔧 Using production fallback');
    return 'https://sec-document-scraper-backend.com';
  }
  
  // Development fallback
  console.log('🔧 Using development fallback - localhost:8080');
  return 'http://localhost:8080';
};

const API_BASE = getApiBase();
console.log('🚀 Final API Base URL:', API_BASE);

export default function ScraperForm() { 
  const [url, setUrl] = useState("");
  const [filingType, setFilingType] = useState("10-K");
  const [selectedSections, setSelectedSections] = useState({});
  const [sectionsData, setSectionsData] = useState({});
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [connectionStatus, setConnectionStatus] = useState('checking');

  // Load sections data on component mount
  useEffect(() => {
    const loadSections = async () => {
      try {
        console.log('📡 Attempting to connect to:', `${API_BASE}/sections`);
        setConnectionStatus('connecting');
        const response = await axios.get(`${API_BASE}/sections`, {
          timeout: 10000 // 10 second timeout
        });
        setSectionsData(response.data);
        setConnectionStatus('connected');
        console.log('✅ Successfully connected to backend');
      } catch (err) {
        console.error("❌ Failed to load sections:", err);
        setError(`Failed to connect to backend API at ${API_BASE}. Please check if the backend service is running.`);
        setConnectionStatus('error');
      }
    };
    loadSections();
  }, []);

  // Auto-detect filing type when URL changes
  useEffect(() => {
    if (url && url.includes("sec.gov") && connectionStatus === 'connected') {
      detectFilingType();
    }
  }, [url, connectionStatus]);

  const detectFilingType = async () => {
    setDetecting(true);
    try {
      const response = await axios.post(`${API_BASE}/detect-filing-type`, {
        filing_url: url
      }, {
        timeout: 5000
      });
      const detectedType = response.data.filing_type;
      setFilingType(detectedType);
      setSelectedSections({}); // Clear selections when type changes
    } catch (err) {
      console.error("Failed to detect filing type:", err);
      // Don't show error for this, just continue with current selection
    } finally {
      setDetecting(false);
    }
  };

  const toggleSection = (sectionId) => {
    setSelectedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const selectAllSections = () => {
    const currentSections = sectionsData[filingType] || {};
    const allSelected = Object.keys(currentSections).reduce((acc, sectionId) => {
      acc[sectionId] = true;
      return acc;
    }, {});
    setSelectedSections(allSelected);
  };

  const clearAllSections = () => {
    setSelectedSections({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const chosen = Object.entries(selectedSections)
      .filter(([, selected]) => selected)
      .map(([sectionId]) => sectionId);

    if (!url) {
      setError("Please enter a SEC filing URL");
      return;
    }

    if (chosen.length === 0) {
      setError("Please select at least one section to scrape");
      return;
    }

    setLoading(true);
    setError("");
    setResults(null);

    try {
      const response = await axios.post(`${API_BASE}/scrape`, {
        filing_url: url,
        sections: chosen
      }, {
        timeout: 120000 // 2 minute timeout for scraping
      });
      setResults(response.data);
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError("Request timed out. The scraping process may take longer for large documents.");
      } else {
        setError(err.response?.data?.error || "An error occurred while scraping");
      }
    } finally {
      setLoading(false);
    }
  };

  const currentSections = sectionsData[filingType] || {};
  const selectedCount = Object.values(selectedSections).filter(Boolean).length;

  // Show connection status if there's an issue
  if (connectionStatus === 'checking') {
    return (
      <div className="scraper-container">
        <div className="scraper-card">
          <div className="loading-state">
            <span className="spinner"></span>
            <p>Connecting to backend service at {API_BASE}...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="scraper-container">
      <div className="scraper-card">
        <header className="scraper-header">
          <h1>SEC Document Section Scraper</h1>
          <p>Extract specific sections from SEC 10-K, 10-Q, and 8-K filings</p>
          {connectionStatus === 'connected' && (
            <div className="connection-status success">
              ✓ Connected to backend service at {API_BASE}
            </div>
          )}
        </header>

        <form onSubmit={handleSubmit} className="scraper-form">
          {/* URL Input */}
          <div className="form-group">
            <label htmlFor="url-input">SEC Filing URL</label>
            <input
              id="url-input"
              type="url"
              placeholder="https://www.sec.gov/Archives/edgar/data/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="url-input"
              required
            />
            <small className="input-help">
              Paste the full URL of the SEC EDGAR filing (must end with .htm or .txt)
            </small>
          </div>

          {/* Filing Type Detection */}
          <div className="form-group">
            <label>Filing Type</label>
            <div className="filing-type-section">
              <div className="filing-type-tabs">
                {["10-K", "10-Q", "8-K"].map(type => (
                  <button
                    key={type}
                    type="button"
                    className={`filing-tab ${filingType === type ? "active" : ""}`}
                    onClick={() => {
                      setFilingType(type);
                      setSelectedSections({});
                    }}
                    disabled={detecting}
                  >
                    {type}
                  </button>
                ))}
              </div>
              {detecting && (
                <div className="detecting-indicator">
                  <span className="spinner"></span>
                  Detecting filing type...
                </div>
              )}
            </div>
          </div>

          {/* Section Selection */}
          <div className="form-group">
            <div className="sections-header">
              <label>Sections to Extract ({selectedCount} selected)</label>
              <div className="section-controls">
                <button
                  type="button"
                  onClick={selectAllSections}
                  className="control-btn select-all"
                  disabled={Object.keys(currentSections).length === 0}
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={clearAllSections}
                  className="control-btn clear-all"
                >
                  Clear All
                </button>
              </div>
            </div>

            <div className="sections-grid">
              {Object.entries(currentSections).map(([sectionId, description]) => (
                <div key={sectionId} className="section-item">
                  <label className="section-label">
                    <input
                      type="checkbox"
                      checked={selectedSections[sectionId] || false}
                      onChange={() => toggleSection(sectionId)}
                      className="section-checkbox"
                    />
                    <div className="section-info">
                      <div className="section-id">{sectionId}</div>
                      <div className="section-description">{description}</div>
                    </div>
                  </label>
                </div>
              ))}
            </div>

            {Object.keys(currentSections).length === 0 && (
              <div className="no-sections">
                No sections available for {filingType}. Please check the filing type.
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            className="submit-btn"
            disabled={loading || selectedCount === 0 || !url || connectionStatus !== 'connected'}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Extracting Sections...
              </>
            ) : (
              `Extract ${selectedCount} Section${selectedCount !== 1 ? 's' : ''}`
            )}
          </button>
        </form>

        {/* Results Display */}
        {results && (
          <div className="results-section">
            <h3>Extraction Results</h3>
            
            <div className="results-summary">
              <div className="summary-stats">
                <div className="stat">
                  <span className="stat-number">{results.summary.successful}</span>
                  <span className="stat-label">Successful</span>
                </div>
                <div className="stat">
                  <span className="stat-number">{results.summary.failed}</span>
                  <span className="stat-label">Failed</span>
                </div>
                <div className="stat">
                  <span className="stat-number">{results.summary.total_sections}</span>
                  <span className="stat-label">Total</span>
                </div>
              </div>
              
              {results.datastore_available && (
                <div className="datastore-status">
                  ✓ Data stored in Google Cloud Datastore
                  {results.project_id && (
                    <span className="project-info">Project: {results.project_id}</span>
                  )}
                </div>
              )}
            </div>

            <div className="results-details">
              {Object.entries(results.results).map(([sectionId, result]) => (
                <div key={sectionId} className={`result-item ${result.status}`}>
                  <div className="result-header">
                    <span className="result-section">{sectionId}</span>
                    <span className={`result-status ${result.status}`}>
                      {result.status === "success" ? "✓" : "✗"}
                    </span>
                  </div>
                  <div className="result-message">{result.message}</div>
                  {result.content_length && (
                    <div className="result-meta">
                      Content length: {result.content_length.toLocaleString()} characters
                    </div>
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
