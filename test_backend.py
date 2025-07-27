#!/usr/bin/env python3
"""
Test script for SEC Document Scraper Backend API
Tests all major endpoints to ensure they're working correctly
"""

import requests
import json
import time
from urllib.parse import urljoin

class BackendTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(urljoin(self.base_url, "/healthz"))
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Datastore available: {data.get('datastore_available', 'Unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        print("\n🔍 Testing root endpoint...")
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint working: {data['service']}")
                print(f"   Version: {data.get('version', 'Unknown')}")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
    
    def test_sections_endpoint(self):
        """Test the sections endpoint"""
        print("\n🔍 Testing sections endpoint...")
        try:
            response = self.session.get(urljoin(self.base_url, "/sections"))
            if response.status_code == 200:
                data = response.json()
                print("✅ Sections endpoint working")
                print(f"   Available filing types: {list(data.keys())}")
                for filing_type, sections in data.items():
                    print(f"   {filing_type}: {len(sections)} sections")
                return True
            else:
                print(f"❌ Sections endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Sections endpoint error: {e}")
            return False
    
    def test_filing_type_detection(self):
        """Test the filing type detection endpoint"""
        print("\n🔍 Testing filing type detection...")
        
        test_cases = [
            ("https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm", "10-K"),
            ("https://www.sec.gov/Archives/edgar/data/1318605/000095017022006034/tsla-20220331.htm", "10-Q"),
            ("https://www.sec.gov/Archives/edgar/data/66600/000149315222016468/form8-k.htm", "8-K")
        ]
        
        for url, expected_type in test_cases:
            try:
                response = self.session.post(
                    urljoin(self.base_url, "/detect-filing-type"),
                    json={"filing_url": url}
                )
                if response.status_code == 200:
                    data = response.json()
                    detected_type = data.get("filing_type")
                    if detected_type == expected_type:
                        print(f"✅ Correctly detected {expected_type}")
                    else:
                        print(f"⚠️  Expected {expected_type}, got {detected_type}")
                else:
                    print(f"❌ Detection failed for {expected_type}: {response.status_code}")
            except Exception as e:
                print(f"❌ Detection error for {expected_type}: {e}")
    
    def test_scrape_endpoint_validation(self):
        """Test the scrape endpoint input validation"""
        print("\n🔍 Testing scrape endpoint validation...")
        
        # Test missing URL
        try:
            response = self.session.post(
                urljoin(self.base_url, "/scrape"),
                json={"sections": ["1"]}
            )
            if response.status_code == 400:
                print("✅ Correctly rejected request without URL")
            else:
                print(f"❌ Should have rejected request without URL: {response.status_code}")
        except Exception as e:
            print(f"❌ Validation test error: {e}")
        
        # Test missing sections
        try:
            response = self.session.post(
                urljoin(self.base_url, "/scrape"),
                json={"filing_url": "https://www.sec.gov/test.htm"}
            )
            if response.status_code == 400:
                print("✅ Correctly rejected request without sections")
            else:
                print(f"❌ Should have rejected request without sections: {response.status_code}")
        except Exception as e:
            print(f"❌ Validation test error: {e}")
        
        # Test invalid URL
        try:
            response = self.session.post(
                urljoin(self.base_url, "/scrape"),
                json={"filing_url": "https://invalid-site.com/test.htm", "sections": ["1"]}
            )
            if response.status_code == 400:
                print("✅ Correctly rejected invalid URL")
            else:
                print(f"❌ Should have rejected invalid URL: {response.status_code}")
        except Exception as e:
            print(f"❌ Validation test error: {e}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SEC Document Scraper Backend Tests")
        print("=" * 50)
        
        # Test all endpoints
        results = []
        results.append(self.test_health_endpoint())
        results.append(self.test_root_endpoint())
        results.append(self.test_sections_endpoint())
        self.test_filing_type_detection()
        self.test_scrape_endpoint_validation()
        
        print("\n" + "=" * 50)
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"🎉 All {total} core tests passed!")
            print("✅ Backend API is working correctly")
            print(f"🌐 Backend running at: {self.base_url}")
        else:
            print(f"⚠️  {passed}/{total} tests passed")
            print("❌ Some issues detected with the backend")
        
        print("\n💡 Note: This test script only validates API endpoints.")
        print("   For full functionality testing, use the frontend interface.")

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test SEC Document Scraper Backend')
    parser.add_argument('--url', default='http://localhost:8080', 
                       help='Backend URL (default: http://localhost:8080)')
    
    args = parser.parse_args()
    
    print(f"Testing backend at: {args.url}")
    print("Make sure the backend is running before running this test.\n")
    
    tester = BackendTester(args.url)
    tester.run_all_tests()

if __name__ == "__main__":
    main() 