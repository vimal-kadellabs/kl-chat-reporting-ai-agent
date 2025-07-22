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
BACKEND_URL = "https://164549cf-bffc-4f80-b8c0-b237f8f26b34.preview.emergentagent.com/api"

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
        """Test /api/properties endpoint - CRITICAL: Should have 140 properties with no null values"""
        try:
            response = self.session.get(f"{self.base_url}/properties")
            
            if response.status_code != 200:
                self.log_test("Properties Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            properties = response.json()
            
            if not isinstance(properties, list):
                self.log_test("Properties Format", False, "Response is not an array")
                return False
                
            # CRITICAL TEST: Should have exactly 140 properties (115 updated + 25 new)
            if len(properties) != 140:
                self.log_test("Properties Count - CRITICAL", False, f"Expected 140 properties (115 updated + 25 new), got {len(properties)}")
                return False
                
            # Verify property structure and data integrity
            null_value_issues = []
            missing_county_count = 0
            new_properties_count = 0
            
            for i, prop in enumerate(properties):
                # Check required fields exist
                required_fields = ["id", "title", "description", "location", "city", "state", "property_type", "reserve_price", "estimated_value"]
                missing_fields = [field for field in required_fields if field not in prop]
                if missing_fields:
                    self.log_test("Properties Structure", False, f"Property {i} missing fields: {missing_fields}")
                    return False
                
                # CRITICAL: Check for null values in required numeric fields
                if prop.get("reserve_price") is None:
                    null_value_issues.append(f"Property {prop.get('id', i)} has null reserve_price")
                if prop.get("estimated_value") is None:
                    null_value_issues.append(f"Property {prop.get('id', i)} has null estimated_value")
                if prop.get("property_type") is None:
                    null_value_issues.append(f"Property {prop.get('id', i)} has null property_type")
                
                # Check county field (should be present for updated properties)
                if prop.get("county") is None:
                    missing_county_count += 1
                
                # Count new properties (assuming they have incremental IDs like prop_16, prop_17, etc.)
                prop_id = prop.get("id", "")
                if prop_id.startswith("prop_") and prop_id.replace("prop_", "").isdigit():
                    prop_num = int(prop_id.replace("prop_", ""))
                    if prop_num >= 16:  # New properties start from prop_16
                        new_properties_count += 1
            
            # Report null value issues - CRITICAL FAILURE
            if null_value_issues:
                self.log_test("Properties Data Integrity - CRITICAL", False, f"Found {len(null_value_issues)} null value issues: {null_value_issues[:5]}")
                return False
            
            # Report county field status
            if missing_county_count > 25:  # Allow some new properties to not have county
                self.log_test("Properties County Field", False, f"Too many properties missing county field: {missing_county_count}")
                return False
            
            # Verify realistic value assignment
            value_issues = []
            for prop in properties[:10]:  # Check first 10 properties
                reserve = prop.get("reserve_price", 0)
                estimated = prop.get("estimated_value", 0)
                if reserve and estimated and reserve >= estimated:
                    value_issues.append(f"Property {prop.get('id')} has reserve_price ({reserve}) >= estimated_value ({estimated})")
            
            if value_issues:
                self.log_test("Properties Value Logic", False, f"Found pricing issues: {value_issues}")
                return False
                    
            self.log_test("Properties Endpoint - ENHANCED", True, 
                         f"✅ 140 properties verified: No null values, {140-missing_county_count} have county field, ~{new_properties_count} new properties, realistic pricing", 
                         {"total": len(properties), "missing_county": missing_county_count, "new_properties": new_properties_count})
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
    
    def test_enhanced_chat_endpoint_top_investors(self):
        """Test /api/chat endpoint with enhanced multiple charts and tables format - TOP INVESTORS"""
        try:
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
                self.log_test("Enhanced Chat - Top Investors", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            chat_response = response.json()
            
            # Verify basic response structure
            required_fields = ["response", "summary_points"]
            missing_fields = [field for field in required_fields if field not in chat_response]
            if missing_fields:
                self.log_test("Enhanced Chat Structure", False, f"Missing basic fields: {missing_fields}")
                return False
            
            # Test NEW ENHANCED FORMAT - Multiple Charts Array
            charts = chat_response.get("charts", [])
            if not isinstance(charts, list):
                self.log_test("Enhanced Charts Format", False, "Charts field is not an array")
                return False
            
            if len(charts) < 2:
                self.log_test("Multiple Charts Generation", False, f"Expected 2-3 charts, got {len(charts)}")
                return False
            
            # Verify chart structure and types
            chart_types_found = []
            for i, chart in enumerate(charts):
                if not isinstance(chart, dict):
                    self.log_test("Chart Structure", False, f"Chart {i} is not a dictionary")
                    return False
                
                chart_required_fields = ["data", "type", "title"]
                chart_missing = [field for field in chart_required_fields if field not in chart]
                if chart_missing:
                    self.log_test("Chart Fields", False, f"Chart {i} missing fields: {chart_missing}")
                    return False
                
                chart_types_found.append(chart["type"])
                
                # Verify chart data is not empty
                if not chart["data"] or not isinstance(chart["data"], list):
                    self.log_test("Chart Data", False, f"Chart {i} has empty or invalid data")
                    return False
                
                # Verify title is meaningful
                if not chart["title"] or len(chart["title"]) < 5:
                    self.log_test("Chart Title", False, f"Chart {i} has empty or too short title")
                    return False
            
            # Verify different chart types
            expected_types = ["bar", "donut", "line"]
            found_expected_types = [t for t in chart_types_found if t in expected_types]
            if len(found_expected_types) < 2:
                self.log_test("Chart Type Variety", False, f"Expected multiple chart types from {expected_types}, got {chart_types_found}")
                return False
            
            # Test NEW ENHANCED FORMAT - Tables Array
            tables = chat_response.get("tables", [])
            if not isinstance(tables, list):
                self.log_test("Enhanced Tables Format", False, "Tables field is not an array")
                return False
            
            if len(tables) < 1:
                self.log_test("Table Generation", False, "Expected at least 1 table")
                return False
            
            # Verify table structure
            for i, table in enumerate(tables):
                if not isinstance(table, dict):
                    self.log_test("Table Structure", False, f"Table {i} is not a dictionary")
                    return False
                
                table_required_fields = ["headers", "rows", "title"]
                table_missing = [field for field in table_required_fields if field not in table]
                if table_missing:
                    self.log_test("Table Fields", False, f"Table {i} missing fields: {table_missing}")
                    return False
                
                # Verify headers and rows
                if not isinstance(table["headers"], list) or len(table["headers"]) == 0:
                    self.log_test("Table Headers", False, f"Table {i} has invalid headers")
                    return False
                
                if not isinstance(table["rows"], list) or len(table["rows"]) == 0:
                    self.log_test("Table Rows", False, f"Table {i} has invalid rows")
                    return False
                
                # Verify row structure matches headers
                for row_idx, row in enumerate(table["rows"]):
                    if not isinstance(row, list) or len(row) != len(table["headers"]):
                        self.log_test("Table Row Structure", False, f"Table {i} row {row_idx} doesn't match header count")
                        return False
            
            # Test BACKWARD COMPATIBILITY - Old format should still exist
            has_old_chart_data = "chart_data" in chat_response
            has_old_chart_type = "chart_type" in chat_response
            
            if not (has_old_chart_data and has_old_chart_type):
                self.log_test("Backward Compatibility", False, "Missing old chart_data or chart_type fields")
                return False
            
            # Verify summary points quality
            summary_points = chat_response.get("summary_points", [])
            if len(summary_points) < 3:
                self.log_test("Summary Points Quality", False, f"Expected 3-4 summary points, got {len(summary_points)}")
                return False
            
            self.log_test("Enhanced Chat - Top Investors", True, 
                         f"✅ Multiple charts: {len(charts)} ({chart_types_found}), Tables: {len(tables)}, Summary: {len(summary_points)} points, Backward compatible", 
                         {"charts_count": len(charts), "chart_types": chart_types_found, "tables_count": len(tables)})
            return True
            
        except Exception as e:
            self.log_test("Enhanced Chat - Top Investors", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_chat_regional_analysis(self):
        """Test /api/chat endpoint with regional analysis query"""
        try:
            test_query = "Which regions had the highest number of bids last month?"
            
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
                self.log_test("Enhanced Chat - Regional", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            chat_response = response.json()
            
            # Verify enhanced format
            charts = chat_response.get("charts", [])
            tables = chat_response.get("tables", [])
            
            if len(charts) < 1:
                self.log_test("Regional Charts", False, "No charts generated for regional query")
                return False
            
            # Check for regional-specific content
            response_text = chat_response.get("response", "").lower()
            regional_keywords = ["region", "city", "location", "market", "geographic"]
            has_regional_content = any(keyword in response_text for keyword in regional_keywords)
            
            if not has_regional_content:
                self.log_test("Regional Content", False, "Response doesn't contain regional analysis content")
                return False
            
            self.log_test("Enhanced Chat - Regional", True, 
                         f"Regional analysis with {len(charts)} charts, {len(tables)} tables", 
                         {"query_type": "regional", "charts": len(charts), "tables": len(tables)})
            return True
            
        except Exception as e:
            self.log_test("Enhanced Chat - Regional", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_chat_upcoming_auctions(self):
        """Test /api/chat endpoint with upcoming auctions query"""
        try:
            test_query = "Show upcoming auctions by city in California."
            
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
                self.log_test("Enhanced Chat - Upcoming Auctions", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            chat_response = response.json()
            
            # Verify response contains auction-specific content
            response_text = chat_response.get("response", "").lower()
            auction_keywords = ["auction", "upcoming", "scheduled", "california"]
            has_auction_content = any(keyword in response_text for keyword in auction_keywords)
            
            if not has_auction_content:
                self.log_test("Auction Content", False, "Response doesn't contain auction-specific content")
                return False
            
            # Verify enhanced format exists
            charts = chat_response.get("charts", [])
            summary_points = chat_response.get("summary_points", [])
            
            if len(summary_points) < 2:
                self.log_test("Auction Summary Points", False, "Insufficient summary points for auction query")
                return False
            
            self.log_test("Enhanced Chat - Upcoming Auctions", True, 
                         f"Auction analysis with {len(charts)} charts, {len(summary_points)} summary points", 
                         {"query_type": "auctions", "charts": len(charts), "summary": len(summary_points)})
            return True
            
        except Exception as e:
            self.log_test("Enhanced Chat - Upcoming Auctions", False, f"Exception: {str(e)}")
            return False
    
    def test_enhanced_chat_property_comparison(self):
        """Test /api/chat endpoint with property type comparison"""
        try:
            test_query = "Compare bidding activity across property types"
            
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
                self.log_test("Enhanced Chat - Property Comparison", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            chat_response = response.json()
            
            # Focus on enhanced format functionality rather than specific content
            # Verify enhanced format exists
            charts = chat_response.get("charts", [])
            tables = chat_response.get("tables", [])
            summary_points = chat_response.get("summary_points", [])
            
            # Verify basic enhanced structure
            if not isinstance(charts, list):
                self.log_test("Enhanced Format - Charts", False, "Charts field is not an array")
                return False
            
            if not isinstance(tables, list):
                self.log_test("Enhanced Format - Tables", False, "Tables field is not an array")
                return False
            
            if not isinstance(summary_points, list) or len(summary_points) < 2:
                self.log_test("Enhanced Format - Summary", False, "Insufficient summary points")
                return False
            
            # Verify response has content
            response_text = chat_response.get("response", "")
            if len(response_text) < 50:
                self.log_test("Response Content", False, "Response too short")
                return False
            
            # For any query, expect at least some visualization or meaningful response
            has_visualizations = len(charts) > 0 or len(tables) > 0
            has_meaningful_response = len(response_text) > 100 and len(summary_points) >= 3
            
            if not (has_visualizations or has_meaningful_response):
                self.log_test("Query Processing", False, "No meaningful visualizations or detailed response")
                return False
            
            self.log_test("Enhanced Chat - Property Comparison", True, 
                         f"Enhanced format working: {len(charts)} charts, {len(tables)} tables, {len(summary_points)} summary points", 
                         {"query_type": "comparison", "enhanced_format": True, "visualizations": len(charts) + len(tables)})
            return True
            
        except Exception as e:
            self.log_test("Enhanced Chat - Property Comparison", False, f"Exception: {str(e)}")
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
        
        # Test in priority order based on review request - ENHANCED TESTING
        tests = [
            ("Health Check", self.test_health_check),
            ("Sample Questions (PRIMARY)", self.test_sample_questions_endpoint),
            ("Users Data (17 users)", self.test_users_endpoint),
            ("Properties Data", self.test_properties_endpoint),
            ("Auctions Data", self.test_auctions_endpoint),
            ("Bids Data", self.test_bids_endpoint),
            ("🔥 ENHANCED: Top Investors Multi-Chart", self.test_enhanced_chat_endpoint_top_investors),
            ("🔥 ENHANCED: Regional Analysis", self.test_enhanced_chat_regional_analysis),
            ("🔥 ENHANCED: Upcoming Auctions", self.test_enhanced_chat_upcoming_auctions),
            ("🔥 ENHANCED: Property Comparison", self.test_enhanced_chat_property_comparison),
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
        
        # Show critical issues - Updated for enhanced testing
        critical_failures = [
            result for result in self.test_results 
            if not result["success"] and any(keyword in result["test"].lower() 
            for keyword in ["enhanced", "sample questions", "chat", "users", "multi-chart", "regional", "auctions", "comparison"])
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