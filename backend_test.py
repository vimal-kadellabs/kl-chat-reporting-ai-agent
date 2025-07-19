#!/usr/bin/env python3
"""
Backend API Testing Suite for Real Estate Auction Analytics
Tests all backend endpoints including the new sample-questions endpoint
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from environment
BACKEND_URL = "https://25387e43-7f9b-4f01-8055-802abc9e4006.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data_sample": str(data)[:200] if data else None
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_health_check(self):
        """Test basic API health"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_test("Health Check", True, f"API responding with status {response.status_code}")
                return True
            else:
                self.log_test("Health Check", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def test_sample_questions_endpoint(self):
        """Test the new /api/sample-questions endpoint - PRIMARY TASK"""
        try:
            response = self.session.get(f"{self.base_url}/sample-questions")
            
            if response.status_code != 200:
                self.log_test("Sample Questions Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Verify response structure
            required_fields = ["questions", "total", "categories"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Sample Questions Structure", False, f"Missing fields: {missing_fields}")
                return False
                
            # Verify questions array
            questions = data.get("questions", [])
            if not isinstance(questions, list):
                self.log_test("Sample Questions Format", False, "Questions field is not an array")
                return False
                
            # Verify we have 24 questions as expected
            if len(questions) != 24:
                self.log_test("Sample Questions Count", False, f"Expected 24 questions, got {len(questions)}")
                return False
                
            # Verify categories structure
            categories = data.get("categories", {})
            expected_categories = [
                "location_insights", "investor_activity", "bidding_trends", 
                "auction_stats", "performance_reports"
            ]
            missing_categories = [cat for cat in expected_categories if cat not in categories]
            if missing_categories:
                self.log_test("Sample Questions Categories", False, f"Missing categories: {missing_categories}")
                return False
                
            # Verify total count matches
            if data.get("total") != len(questions):
                self.log_test("Sample Questions Total", False, f"Total count {data.get('total')} doesn't match questions length {len(questions)}")
                return False
                
            self.log_test("Sample Questions Endpoint", True, f"Successfully returned {len(questions)} questions with 5 categories", data)
            return True
            
        except Exception as e:
            self.log_test("Sample Questions Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_users_endpoint(self):
        """Test /api/users endpoint - should return 17 users"""
        try:
            response = self.session.get(f"{self.base_url}/users")
            
            if response.status_code != 200:
                self.log_test("Users Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            users = response.json()
            
            if not isinstance(users, list):
                self.log_test("Users Format", False, "Response is not an array")
                return False
                
            # Verify we have 17 users as expected
            if len(users) != 17:
                self.log_test("Users Count", False, f"Expected 17 users, got {len(users)}")
                return False
                
            # Verify user structure
            if users:
                user = users[0]
                required_fields = ["id", "email", "name", "location", "profile_verified", "success_rate", "total_bids", "won_auctions"]
                missing_fields = [field for field in required_fields if field not in user]
                if missing_fields:
                    self.log_test("Users Structure", False, f"Missing user fields: {missing_fields}")
                    return False
                    
            self.log_test("Users Endpoint", True, f"Successfully returned {len(users)} users with complete data", users[0] if users else None)
            return True
            
        except Exception as e:
            self.log_test("Users Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_properties_endpoint(self):
        """Test /api/properties endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/properties")
            
            if response.status_code != 200:
                self.log_test("Properties Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            properties = response.json()
            
            if not isinstance(properties, list):
                self.log_test("Properties Format", False, "Response is not an array")
                return False
                
            if len(properties) == 0:
                self.log_test("Properties Count", False, "No properties returned")
                return False
                
            # Verify property structure
            if properties:
                prop = properties[0]
                required_fields = ["id", "title", "description", "location", "city", "state", "property_type", "reserve_price", "estimated_value"]
                missing_fields = [field for field in required_fields if field not in prop]
                if missing_fields:
                    self.log_test("Properties Structure", False, f"Missing property fields: {missing_fields}")
                    return False
                    
            self.log_test("Properties Endpoint", True, f"Successfully returned {len(properties)} properties with complete data", properties[0] if properties else None)
            return True
            
        except Exception as e:
            self.log_test("Properties Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_auctions_endpoint(self):
        """Test /api/auctions endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/auctions")
            
            if response.status_code != 200:
                self.log_test("Auctions Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            auctions = response.json()
            
            if not isinstance(auctions, list):
                self.log_test("Auctions Format", False, "Response is not an array")
                return False
                
            if len(auctions) == 0:
                self.log_test("Auctions Count", False, "No auctions returned")
                return False
                
            # Verify auction structure
            if auctions:
                auction = auctions[0]
                required_fields = ["id", "property_id", "title", "start_time", "end_time", "status", "starting_bid", "current_highest_bid", "total_bids"]
                missing_fields = [field for field in required_fields if field not in auction]
                if missing_fields:
                    self.log_test("Auctions Structure", False, f"Missing auction fields: {missing_fields}")
                    return False
                    
            self.log_test("Auctions Endpoint", True, f"Successfully returned {len(auctions)} auctions with complete data", auctions[0] if auctions else None)
            return True
            
        except Exception as e:
            self.log_test("Auctions Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_bids_endpoint(self):
        """Test /api/bids endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/bids")
            
            if response.status_code != 200:
                self.log_test("Bids Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            bids = response.json()
            
            if not isinstance(bids, list):
                self.log_test("Bids Format", False, "Response is not an array")
                return False
                
            if len(bids) == 0:
                self.log_test("Bids Count", False, "No bids returned")
                return False
                
            # Verify bid structure
            if bids:
                bid = bids[0]
                required_fields = ["id", "auction_id", "property_id", "investor_id", "bid_amount", "bid_time", "status"]
                missing_fields = [field for field in required_fields if field not in bid]
                if missing_fields:
                    self.log_test("Bids Structure", False, f"Missing bid fields: {missing_fields}")
                    return False
                    
            self.log_test("Bids Endpoint", True, f"Successfully returned {len(bids)} bids with complete data", bids[0] if bids else None)
            return True
            
        except Exception as e:
            self.log_test("Bids Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_chat_endpoint_with_sample_question(self):
        """Test /api/chat endpoint with a sample question - CORE FUNCTIONALITY"""
        try:
            # Use one of the sample questions
            test_query = "Who are the top 5 investors by bid amount?"
            
            payload = {
                "message": test_query,
                "user_id": "test_user"
            }
            
            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("Chat Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            chat_response = response.json()
            
            # Verify response structure
            required_fields = ["response", "summary_points"]
            missing_fields = [field for field in required_fields if field not in chat_response]
            if missing_fields:
                self.log_test("Chat Response Structure", False, f"Missing fields: {missing_fields}")
                return False
                
            # Verify response content
            if not chat_response.get("response"):
                self.log_test("Chat Response Content", False, "Empty response field")
                return False
                
            # Verify summary points
            summary_points = chat_response.get("summary_points", [])
            if not isinstance(summary_points, list) or len(summary_points) == 0:
                self.log_test("Chat Summary Points", False, "Missing or empty summary_points")
                return False
                
            # Check for chart data (optional but expected for this query)
            has_chart_data = "chart_data" in chat_response and chat_response["chart_data"]
            chart_info = f"Chart data: {'Present' if has_chart_data else 'Not present'}"
            
            self.log_test("Chat Endpoint", True, f"Successfully processed query. Response length: {len(chat_response['response'])}, Summary points: {len(summary_points)}. {chart_info}", chat_response)
            return True
            
        except Exception as e:
            self.log_test("Chat Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_force_init_data_endpoint(self):
        """Test /api/force-init-data endpoint"""
        try:
            response = self.session.post(f"{self.base_url}/force-init-data")
            
            if response.status_code != 200:
                self.log_test("Force Init Data", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            result = response.json()
            
            if "message" not in result:
                self.log_test("Force Init Data Response", False, "Missing message field in response")
                return False
                
            self.log_test("Force Init Data", True, f"Data initialization: {result.get('message')}", result)
            return True
            
        except Exception as e:
            self.log_test("Force Init Data", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test in priority order based on review request
        tests = [
            ("Health Check", self.test_health_check),
            ("Sample Questions (PRIMARY)", self.test_sample_questions_endpoint),
            ("Users Data (17 users)", self.test_users_endpoint),
            ("Properties Data", self.test_properties_endpoint),
            ("Auctions Data", self.test_auctions_endpoint),
            ("Bids Data", self.test_bids_endpoint),
            ("Chat with Sample Question (CORE)", self.test_chat_endpoint_with_sample_question),
            ("Force Init Data", self.test_force_init_data_endpoint),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            if test_func():
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        # Show critical issues
        critical_failures = [
            result for result in self.test_results 
            if not result["success"] and any(keyword in result["test"].lower() 
            for keyword in ["sample questions", "chat", "users"])
        ]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_failures)}):")
            for test in critical_failures:
                print(f"   • {test['test']}: {test['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n✅ All backend tests passed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Some backend tests failed. Check details above.")
        sys.exit(1)