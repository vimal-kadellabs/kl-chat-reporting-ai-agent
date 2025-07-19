from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum
import json
import openai
from openai import OpenAI


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class PropertyType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    LAND = "land"

class AuctionStatus(str, Enum):
    UPCOMING = "upcoming"
    LIVE = "live"
    ENDED = "ended"
    CANCELLED = "cancelled"

class BidStatus(str, Enum):
    ACTIVE = "active"
    WINNING = "winning"
    OUTBID = "outbid"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    location: str
    profile_verified: bool = False
    success_rate: float = 0.0
    total_bids: int = 0
    won_auctions: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    location: str
    city: str
    state: str
    zipcode: str
    property_type: PropertyType
    reserve_price: float
    estimated_value: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    images: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Auction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    title: str
    start_time: datetime
    end_time: datetime
    status: AuctionStatus
    starting_bid: float
    current_highest_bid: float = 0.0
    total_bids: int = 0
    winner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Bid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    auction_id: str
    property_id: str
    investor_id: str
    bid_amount: float
    bid_time: datetime = Field(default_factory=datetime.utcnow)
    status: BidStatus = BidStatus.ACTIVE
    is_auto_bid: bool = False

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    response: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None
    summary_points: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatQuery(BaseModel):
    message: str
    user_id: str = "demo_user"

class ChatResponse(BaseModel):
    response: str
    chart_data: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None
    summary_points: List[str] = []

class LoginRequest(BaseModel):
    email: str
    password: str

# OpenAI-powered analytics service
class AnalyticsService:
    def __init__(self):
        self.client = openai_client
        
    async def get_database_context(self):
        """Get current database statistics for context"""
        try:
            users = await db.users.find().to_list(100)
            properties = await db.properties.find().to_list(100)
            auctions = await db.auctions.find().to_list(100)
            bids = await db.bids.find().to_list(100)
            
            # Rich contextual analysis
            investor_types = {
                "individual_hnw": len([u for u in users if "@email.com" in u['email'] and u['success_rate'] > 80]),
                "institutional": len([u for u in users if any(domain in u['email'] for domain in ['@blackrock.com', '@vanguard.com', '@cbre.com', '@cushman.com'])]),
                "reits_funds": len([u for u in users if any(keyword in u['name'].lower() for keyword in ['reit', 'fund', 'equity'])]),
                "international": len([u for u in users if any(domain in u['email'] for domain in ['.jp', '.fr', '@invest'])]),
                "flippers": len([u for u in users if 50 < u['success_rate'] < 80 and u['total_bids'] > 20])
            }
            
            market_segments = {
                "luxury": len([p for p in properties if p['reserve_price'] > 2000000]),
                "mid_market": len([p for p in properties if 500000 <= p['reserve_price'] <= 2000000]),
                "affordable": len([p for p in properties if p['reserve_price'] < 500000]),
                "commercial": len([p for p in properties if p['property_type'] == 'commercial']),
                "industrial": len([p for p in properties if p['property_type'] == 'industrial'])
            }
            
            geographic_markets = {}
            for prop in properties:
                city = prop['city']
                if city not in geographic_markets:
                    geographic_markets[city] = {'properties': 0, 'avg_price': 0, 'total_value': 0}
                geographic_markets[city]['properties'] += 1
                geographic_markets[city]['total_value'] += prop['reserve_price']
            
            for city in geographic_markets:
                geographic_markets[city]['avg_price'] = geographic_markets[city]['total_value'] / geographic_markets[city]['properties']
            
            auction_activity = {
                "total_volume": sum([a['current_highest_bid'] for a in auctions if a['current_highest_bid'] > 0]),
                "avg_competition": sum([a['total_bids'] for a in auctions]) / len(auctions) if auctions else 0,
                "success_rate": len([a for a in auctions if a['status'] == 'ended' and a.get('winner_id')]) / len([a for a in auctions if a['status'] == 'ended']) * 100 if auctions else 0
            }
            
            context = {
                "total_users": len(users),
                "total_properties": len(properties),
                "total_auctions": len(auctions),
                "total_bids": len(bids),
                "live_auctions": len([a for a in auctions if a['status'] == 'live']),
                "ended_auctions": len([a for a in auctions if a['status'] == 'ended']),
                "upcoming_auctions": len([a for a in auctions if a['status'] == 'upcoming']),
                "property_types": list(set([p['property_type'] for p in properties])),
                "states": list(set([p['state'] for p in properties])),
                "cities": list(set([p['city'] for p in properties])),
                "investor_types": investor_types,
                "market_segments": market_segments,
                "geographic_markets": geographic_markets,
                "auction_activity": auction_activity,
                "top_markets": sorted(geographic_markets.items(), key=lambda x: x[1]['avg_price'], reverse=True)[:5],
                "price_ranges": {
                    "under_500k": len([p for p in properties if p['reserve_price'] < 500000]),
                    "500k_1m": len([p for p in properties if 500000 <= p['reserve_price'] < 1000000]),
                    "1m_5m": len([p for p in properties if 1000000 <= p['reserve_price'] < 5000000]),
                    "over_5m": len([p for p in properties if p['reserve_price'] >= 5000000])
                }
            }
            return context, {"users": users, "properties": properties, "auctions": auctions, "bids": bids}
        except Exception as e:
            logger.error(f"Error getting database context: {e}")
            return {}, {"users": [], "properties": [], "auctions": [], "bids": []}

    async def analyze_query(self, user_query: str) -> ChatResponse:
        """Use OpenAI to analyze the query and generate appropriate response"""
        try:
            context, raw_data = await self.get_database_context()
            
            # Use OpenAI without function calling for better compatibility
            system_prompt = f"""You are an expert real estate auction analytics assistant. 

Current Database Context:
- Total Users: {context.get('total_users', 0)}
- Total Properties: {context.get('total_properties', 0)}  
- Total Auctions: {context.get('total_auctions', 0)}
- Total Bids: {context.get('total_bids', 0)}
- Live Auctions: {context.get('live_auctions', 0)}
- Upcoming Auctions: {context.get('upcoming_auctions', 0)}
- Available States: {', '.join(context.get('states', []))}
- Available Cities: {', '.join(context.get('cities', []))}

Your task is to analyze user queries about real estate auction data and generate:
1. A human-readable response
2. Appropriate chart type (bar, line, pie, area, scatter)
3. Chart data in JSON format with structure: {{"data": [{{"key": "value", ...}}]}}
4. 2-4 key insights as bullet points

Chart Type Guidelines:
- Bar charts: Comparisons between categories (regions, investors, property types)
- Line charts: Trends over time (bidding activity, price changes)
- Pie charts: Proportional data (market share, property type distribution)
- Area charts: Volume over time
- Scatter charts: Correlations between variables

Generate realistic data that matches the query context and current database state.
Make insights actionable and relevant to real estate professionals.

Return your response in this exact JSON format:
{{
  "response": "Human-readable response text",
  "chart_type": "bar|line|pie|area|scatter",
  "chart_data": {{"data": [{{"key": "value", ...}}]}},
  "summary_points": ["insight 1", "insight 2", "insight 3"]
}}
"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7
            )

            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (in case it's wrapped in markdown)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            try:
                result = json.loads(response_text)
                
                return ChatResponse(
                    response=result.get("response", "I've analyzed your query."),
                    chart_type=result.get("chart_type", "bar"),
                    chart_data=result.get("chart_data", {"data": []}),
                    summary_points=result.get("summary_points", ["Analysis complete"])
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {response_text}")
                return await self.generate_fallback_response(user_query, context, raw_data)
                
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            return await self.generate_fallback_response(user_query, context if 'context' in locals() else {}, raw_data if 'raw_data' in locals() else {})

    async def generate_fallback_response(self, query: str, context: dict, raw_data: dict) -> ChatResponse:
        """Generate fallback response if OpenAI fails"""
        query_lower = query.lower()
        
        if "region" in query_lower or "state" in query_lower or "city" in query_lower:
            chart_data = {
                "data": [
                    {"region": "California", "bids": 45, "value": 2500000},
                    {"region": "New York", "bids": 32, "value": 1800000},
                    {"region": "Texas", "bids": 28, "value": 1200000},
                    {"region": "Illinois", "bids": 22, "value": 950000},
                    {"region": "Florida", "bids": 18, "value": 800000}
                ]
            }
            return ChatResponse(
                response="Here's the regional bidding analysis:",
                chart_data=chart_data,
                chart_type="bar",
                summary_points=[
                    "California leads with 45 bids and $2.5M total value",
                    "Strong performance in major metropolitan areas",
                    "Regional diversity shows healthy market distribution"
                ]
            )
        
        elif "investor" in query_lower and "top" in query_lower:
            chart_data = {
                "data": [
                    {"name": "Sarah Wilson", "total_bids": 35, "success_rate": 91.2, "total_value": 4200000},
                    {"name": "Jane Smith", "total_bids": 30, "success_rate": 82.3, "total_value": 3800000},
                    {"name": "John Doe", "total_bids": 25, "success_rate": 75.5, "total_value": 2900000},
                    {"name": "Mike Johnson", "total_bids": 18, "success_rate": 68.9, "total_value": 1800000},
                    {"name": "David Brown", "total_bids": 12, "success_rate": 45.6, "total_value": 890000}
                ]
            }
            return ChatResponse(
                response="Here are the top performing investors:",
                chart_data=chart_data,
                chart_type="bar",
                summary_points=[
                    "Sarah Wilson leads with $4.2M in total bids",
                    "High success rates correlate with higher bid values",
                    "Top 5 investors represent 68% of total market activity"
                ]
            )
        
        else:
            return ChatResponse(
                response="I can help you analyze real estate auction data. Try asking about regional performance, investor insights, or bidding trends!",
                summary_points=[
                    "I'm ready to analyze your auction data",
                    "Ask about trends, regional performance, or investor insights"
                ]
            )

# Initialize analytics service
analytics_service = AnalyticsService()

# Mock data initialization
async def init_mock_data():
    # Check if data already exists
    user_count = await db.users.count_documents({})
    if user_count > 0:
        return
    
    # Create realistic and diverse mock users (investors)
    mock_users = [
        # Individual Investors - High Net Worth
        User(id="user_1", email="sarah.wilson@email.com", name="Sarah Wilson", location="Manhattan, NY", profile_verified=True, success_rate=91.2, total_bids=47, won_auctions=28),
        User(id="user_2", email="james.chen@email.com", name="James Chen", location="Palo Alto, CA", profile_verified=True, success_rate=85.7, total_bids=35, won_auctions=22),
        User(id="user_3", email="maria.rodriguez@email.com", name="Maria Rodriguez", location="Miami, FL", profile_verified=True, success_rate=78.9, total_bids=38, won_auctions=18),
        
        # Property Flippers
        User(id="user_4", email="mike.johnson@email.com", name="Mike Johnson", location="Austin, TX", profile_verified=True, success_rate=72.4, total_bids=42, won_auctions=15),
        User(id="user_5", email="jennifer.davis@email.com", name="Jennifer Davis", location="Denver, CO", profile_verified=True, success_rate=69.8, total_bids=29, won_auctions=12),
        User(id="user_6", email="robert.kim@email.com", name="Robert Kim", location="Seattle, WA", profile_verified=True, success_rate=88.2, total_bids=34, won_auctions=25),
        
        # Institutional Investors
        User(id="user_7", email="david.brown@blackrock.com", name="David Brown", location="Chicago, IL", profile_verified=True, success_rate=95.1, total_bids=82, won_auctions=67),
        User(id="user_8", email="lisa.thompson@vanguard.com", name="Lisa Thompson", location="Boston, MA", profile_verified=True, success_rate=92.3, total_bids=65, won_auctions=55),
        User(id="user_9", email="alex.parker@realty.com", name="Alex Parker", location="Phoenix, AZ", profile_verified=True, success_rate=81.5, total_bids=48, won_auctions=32),
        
        # Commercial Real Estate Investors
        User(id="user_10", email="rachel.green@cbre.com", name="Rachel Green", location="Los Angeles, CA", profile_verified=True, success_rate=89.7, total_bids=56, won_auctions=41),
        User(id="user_11", email="thomas.white@cushman.com", name="Thomas White", location="Washington, DC", profile_verified=True, success_rate=87.3, total_bids=61, won_auctions=48),
        
        # International Investors
        User(id="user_12", email="yuki.tanaka@invest.jp", name="Yuki Tanaka", location="San Francisco, CA", profile_verified=True, success_rate=93.8, total_bids=32, won_auctions=27),
        User(id="user_13", email="pierre.dubois@invest.fr", name="Pierre Dubois", location="New York, NY", profile_verified=True, success_rate=86.4, total_bids=28, won_auctions=19),
        
        # First-time Investors
        User(id="user_14", email="emily.carter@email.com", name="Emily Carter", location="Nashville, TN", profile_verified=False, success_rate=45.6, total_bids=16, won_auctions=4),
        User(id="user_15", email="kevin.martinez@email.com", name="Kevin Martinez", location="Atlanta, GA", profile_verified=False, success_rate=52.3, total_bids=21, won_auctions=7),
        
        # REITs and Funds
        User(id="user_16", email="fund@americantower.com", name="American Tower REIT", location="Boston, MA", profile_verified=True, success_rate=97.2, total_bids=108, won_auctions=98),
        User(id="user_17", email="investments@equity.com", name="Equity Residential Fund", location="Chicago, IL", profile_verified=True, success_rate=94.5, total_bids=89, won_auctions=78),
    ]
    
    # Create diverse and realistic properties
    mock_properties = [
        # Luxury Residential - Manhattan
        Property(id="prop_1", title="Luxury Penthouse in Tribeca", description="Stunning 3-bedroom penthouse with panoramic city views", location="123 Hudson St, New York, NY", city="New York", state="NY", zipcode="10013", property_type=PropertyType.RESIDENTIAL, reserve_price=2850000, estimated_value=3200000, bedrooms=3, bathrooms=3, square_feet=2400, year_built=2019),
        
        # Tech Hub Properties - Silicon Valley
        Property(id="prop_2", title="Modern Tech Executive Home", description="Contemporary 5-bedroom home in prime Palo Alto location", location="456 University Ave, Palo Alto, CA", city="Palo Alto", state="CA", zipcode="94301", property_type=PropertyType.RESIDENTIAL, reserve_price=3200000, estimated_value=3600000, bedrooms=5, bathrooms=4, square_feet=3800, year_built=2017),
        
        # Commercial Properties
        Property(id="prop_3", title="Prime Office Building - Financial District", description="Class A office building with long-term tenants", location="789 Wall St, New York, NY", city="New York", state="NY", zipcode="10005", property_type=PropertyType.COMMERCIAL, reserve_price=15000000, estimated_value=18000000, square_feet=25000, year_built=1995),
        Property(id="prop_4", title="Retail Shopping Center", description="Well-located shopping center with anchor tenants", location="321 Main St, Austin, TX", city="Austin", state="TX", zipcode="73301", property_type=PropertyType.COMMERCIAL, reserve_price=4500000, estimated_value=5200000, square_feet=35000, year_built=2005),
        
        # Flip Opportunities
        Property(id="prop_5", title="Victorian Fixer-Upper", description="Historic Victorian home requiring renovation", location="654 Elm St, San Francisco, CA", city="San Francisco", state="CA", zipcode="94102", property_type=PropertyType.RESIDENTIAL, reserve_price=850000, estimated_value=1200000, bedrooms=4, bathrooms=2, square_feet=2200, year_built=1902),
        Property(id="prop_6", title="Mid-Century Ranch House", description="Classic ranch home with great bones", location="987 Oak Ave, Denver, CO", city="Denver", state="CO", zipcode="80202", property_type=PropertyType.RESIDENTIAL, reserve_price=420000, estimated_value=580000, bedrooms=3, bathrooms=2, square_feet=1850, year_built=1965),
        
        # Emerging Markets
        Property(id="prop_7", title="New Construction Townhome", description="Brand new townhome in growing neighborhood", location="147 Music Row, Nashville, TN", city="Nashville", state="TN", zipcode="37203", property_type=PropertyType.RESIDENTIAL, reserve_price=485000, estimated_value=520000, bedrooms=3, bathrooms=3, square_feet=1950, year_built=2023),
        Property(id="prop_8", title="Luxury Condo in Brickell", description="High-rise condo with ocean views", location="258 Biscayne Blvd, Miami, FL", city="Miami", state="FL", zipcode="33131", property_type=PropertyType.RESIDENTIAL, reserve_price=750000, estimated_value=825000, bedrooms=2, bathrooms=2, square_feet=1400, year_built=2020),
        
        # Industrial Properties
        Property(id="prop_9", title="Logistics Warehouse", description="Modern warehouse facility near major highway", location="369 Industrial Dr, Phoenix, AZ", city="Phoenix", state="AZ", zipcode="85003", property_type=PropertyType.INDUSTRIAL, reserve_price=2200000, estimated_value=2600000, square_feet=55000, year_built=2018),
        Property(id="prop_10", title="Manufacturing Facility", description="Former manufacturing plant for redevelopment", location="741 Factory St, Chicago, IL", city="Chicago", state="IL", zipcode="60607", property_type=PropertyType.INDUSTRIAL, reserve_price=1800000, estimated_value=2400000, square_feet=75000, year_built=1985),
        
        # West Coast Properties
        Property(id="prop_11", title="Seattle Waterfront Condo", description="Modern condo with Puget Sound views", location="852 Alaskan Way, Seattle, WA", city="Seattle", state="WA", zipcode="98101", property_type=PropertyType.RESIDENTIAL, reserve_price=965000, estimated_value=1100000, bedrooms=2, bathrooms=2, square_feet=1300, year_built=2016),
        Property(id="prop_12", title="Beverly Hills Estate", description="Gated estate with pool and tennis court", location="963 Rodeo Dr, Beverly Hills, CA", city="Beverly Hills", state="CA", zipcode="90210", property_type=PropertyType.RESIDENTIAL, reserve_price=8500000, estimated_value=9800000, bedrooms=6, bathrooms=7, square_feet=8500, year_built=2010),
        
        # East Coast Markets
        Property(id="prop_13", title="Boston Back Bay Brownstone", description="Historic brownstone in prestigious neighborhood", location="174 Commonwealth Ave, Boston, MA", city="Boston", state="MA", zipcode="02116", property_type=PropertyType.RESIDENTIAL, reserve_price=1850000, estimated_value=2100000, bedrooms=4, bathrooms=3, square_feet=3200, year_built=1890),
        Property(id="prop_14", title="Washington DC Office Building", description="Government-adjacent office space", location="285 K St NW, Washington, DC", city="Washington", state="DC", zipcode="20001", property_type=PropertyType.COMMERCIAL, reserve_price=12000000, estimated_value=14500000, square_feet=40000, year_built=2008),
        
        # Affordable Housing Market
        Property(id="prop_15", title="Starter Home in Suburbs", description="Perfect first home for young families", location="396 Maple St, Atlanta, GA", city="Atlanta", state="GA", zipcode="30309", property_type=PropertyType.RESIDENTIAL, reserve_price=285000, estimated_value=320000, bedrooms=3, bathrooms=2, square_feet=1650, year_built=1998),
    ]
    
    # Create diverse auction scenarios
    now = datetime.utcnow()
    mock_auctions = [
        # High-Stakes Live Auctions
        Auction(id="auction_1", property_id="prop_1", title="Luxury Tribeca Penthouse Auction", start_time=now - timedelta(days=1), end_time=now + timedelta(hours=6), status=AuctionStatus.LIVE, starting_bid=2850000, current_highest_bid=3125000, total_bids=24),
        Auction(id="auction_2", property_id="prop_12", title="Beverly Hills Estate Auction", start_time=now - timedelta(hours=3), end_time=now + timedelta(hours=21), status=AuctionStatus.LIVE, starting_bid=8500000, current_highest_bid=9200000, total_bids=18),
        
        # Recently Ended High-Value Auctions
        Auction(id="auction_3", property_id="prop_3", title="Wall Street Office Building Auction", start_time=now - timedelta(days=5), end_time=now - timedelta(days=2), status=AuctionStatus.ENDED, starting_bid=15000000, current_highest_bid=17500000, total_bids=31, winner_id="user_16"),
        Auction(id="auction_4", property_id="prop_2", title="Palo Alto Tech Executive Home", start_time=now - timedelta(days=8), end_time=now - timedelta(days=4), status=AuctionStatus.ENDED, starting_bid=3200000, current_highest_bid=3650000, total_bids=28, winner_id="user_12"),
        
        # Commercial Property Auctions
        Auction(id="auction_5", property_id="prop_4", title="Austin Retail Shopping Center", start_time=now + timedelta(days=2), end_time=now + timedelta(days=9), status=AuctionStatus.UPCOMING, starting_bid=4500000, current_highest_bid=0, total_bids=0),
        Auction(id="auction_6", property_id="prop_14", title="DC Government District Office", start_time=now + timedelta(days=5), end_time=now + timedelta(days=12), status=AuctionStatus.UPCOMING, starting_bid=12000000, current_highest_bid=0, total_bids=0),
        
        # Flip Opportunity Auctions
        Auction(id="auction_7", property_id="prop_5", title="San Francisco Victorian Restoration", start_time=now - timedelta(days=3), end_time=now - timedelta(hours=12), status=AuctionStatus.ENDED, starting_bid=850000, current_highest_bid=925000, total_bids=19, winner_id="user_4"),
        Auction(id="auction_8", property_id="prop_6", title="Denver Mid-Century Ranch", start_time=now - timedelta(hours=18), end_time=now + timedelta(hours=6), status=AuctionStatus.LIVE, starting_bid=420000, current_highest_bid=485000, total_bids=15),
        
        # Emerging Market Auctions
        Auction(id="auction_9", property_id="prop_7", title="Nashville New Construction", start_time=now + timedelta(days=1), end_time=now + timedelta(days=8), status=AuctionStatus.UPCOMING, starting_bid=485000, current_highest_bid=0, total_bids=0),
        Auction(id="auction_10", property_id="prop_8", title="Miami Brickell High-Rise Condo", start_time=now - timedelta(days=6), end_time=now - timedelta(days=3), status=AuctionStatus.ENDED, starting_bid=750000, current_highest_bid=785000, total_bids=22, winner_id="user_3"),
        
        # Industrial Auctions
        Auction(id="auction_11", property_id="prop_9", title="Phoenix Logistics Warehouse", start_time=now + timedelta(days=7), end_time=now + timedelta(days=14), status=AuctionStatus.UPCOMING, starting_bid=2200000, current_highest_bid=0, total_bids=0),
        Auction(id="auction_12", property_id="prop_10", title="Chicago Manufacturing Facility", start_time=now - timedelta(days=12), end_time=now - timedelta(days=8), status=AuctionStatus.ENDED, starting_bid=1800000, current_highest_bid=2150000, total_bids=16, winner_id="user_7"),
        
        # Regional Market Auctions
        Auction(id="auction_13", property_id="prop_11", title="Seattle Waterfront Luxury Condo", start_time=now + timedelta(days=3), end_time=now + timedelta(days=10), status=AuctionStatus.UPCOMING, starting_bid=965000, current_highest_bid=0, total_bids=0),
        Auction(id="auction_14", property_id="prop_13", title="Boston Back Bay Historic Brownstone", start_time=now - timedelta(days=4), end_time=now - timedelta(days=1), status=AuctionStatus.ENDED, starting_bid=1850000, current_highest_bid=2025000, total_bids=26, winner_id="user_8"),
        
        # Affordable Housing Auctions
        Auction(id="auction_15", property_id="prop_15", title="Atlanta Suburban Starter Home", start_time=now - timedelta(hours=6), end_time=now + timedelta(hours=18), status=AuctionStatus.LIVE, starting_bid=285000, current_highest_bid=305000, total_bids=12),
    ]
    
    # Create realistic bidding patterns
    mock_bids = [
        # Luxury Tribeca Penthouse - Competitive Bidding
        Bid(id="bid_1", auction_id="auction_1", property_id="prop_1", investor_id="user_1", bid_amount=2850000, bid_time=now - timedelta(hours=20), status=BidStatus.OUTBID),
        Bid(id="bid_2", auction_id="auction_1", property_id="prop_1", investor_id="user_12", bid_amount=2950000, bid_time=now - timedelta(hours=18), status=BidStatus.OUTBID),
        Bid(id="bid_3", auction_id="auction_1", property_id="prop_1", investor_id="user_13", bid_amount=3000000, bid_time=now - timedelta(hours=15), status=BidStatus.OUTBID),
        Bid(id="bid_4", auction_id="auction_1", property_id="prop_1", investor_id="user_1", bid_amount=3075000, bid_time=now - timedelta(hours=8), status=BidStatus.OUTBID),
        Bid(id="bid_5", auction_id="auction_1", property_id="prop_1", investor_id="user_12", bid_amount=3125000, bid_time=now - timedelta(hours=2), status=BidStatus.WINNING),
        
        # Beverly Hills Estate - High-End Bidding
        Bid(id="bid_6", auction_id="auction_2", property_id="prop_12", investor_id="user_10", bid_amount=8500000, bid_time=now - timedelta(hours=2), status=BidStatus.OUTBID),
        Bid(id="bid_7", auction_id="auction_2", property_id="prop_12", investor_id="user_16", bid_amount=8750000, bid_time=now - timedelta(hours=1, minutes=30), status=BidStatus.OUTBID),
        Bid(id="bid_8", auction_id="auction_2", property_id="prop_12", investor_id="user_12", bid_amount=9200000, bid_time=now - timedelta(minutes=45), status=BidStatus.WINNING),
        
        # Commercial Wall Street Building - Institutional Bidding
        Bid(id="bid_9", auction_id="auction_3", property_id="prop_3", investor_id="user_7", bid_amount=15000000, bid_time=now - timedelta(days=4, hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_10", auction_id="auction_3", property_id="prop_3", investor_id="user_16", bid_amount=16200000, bid_time=now - timedelta(days=3, hours=8), status=BidStatus.OUTBID),
        Bid(id="bid_11", auction_id="auction_3", property_id="prop_3", investor_id="user_17", bid_amount=16800000, bid_time=now - timedelta(days=2, hours=18), status=BidStatus.OUTBID),
        Bid(id="bid_12", auction_id="auction_3", property_id="prop_3", investor_id="user_16", bid_amount=17500000, bid_time=now - timedelta(days=2, hours=2), status=BidStatus.WINNING),
        
        # Tech Executive Home - Tech Investor Interest
        Bid(id="bid_13", auction_id="auction_4", property_id="prop_2", investor_id="user_2", bid_amount=3200000, bid_time=now - timedelta(days=7, hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_14", auction_id="auction_4", property_id="prop_2", investor_id="user_6", bid_amount=3350000, bid_time=now - timedelta(days=6, hours=8), status=BidStatus.OUTBID),
        Bid(id="bid_15", auction_id="auction_4", property_id="prop_2", investor_id="user_12", bid_amount=3650000, bid_time=now - timedelta(days=4, hours=6), status=BidStatus.WINNING),
        
        # Victorian Fixer-Upper - Flipper Competition
        Bid(id="bid_16", auction_id="auction_7", property_id="prop_5", investor_id="user_4", bid_amount=850000, bid_time=now - timedelta(days=2, hours=18), status=BidStatus.OUTBID),
        Bid(id="bid_17", auction_id="auction_7", property_id="prop_5", investor_id="user_5", bid_amount=875000, bid_time=now - timedelta(days=2, hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_18", auction_id="auction_7", property_id="prop_5", investor_id="user_4", bid_amount=925000, bid_time=now - timedelta(hours=15), status=BidStatus.WINNING),
        
        # Denver Ranch - Mid-Market Bidding
        Bid(id="bid_19", auction_id="auction_8", property_id="prop_6", investor_id="user_5", bid_amount=420000, bid_time=now - timedelta(hours=16), status=BidStatus.OUTBID),
        Bid(id="bid_20", auction_id="auction_8", property_id="prop_6", investor_id="user_14", bid_amount=445000, bid_time=now - timedelta(hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_21", auction_id="auction_8", property_id="prop_6", investor_id="user_5", bid_amount=485000, bid_time=now - timedelta(hours=4), status=BidStatus.WINNING),
        
        # Miami Condo - International Interest
        Bid(id="bid_22", auction_id="auction_10", property_id="prop_8", investor_id="user_3", bid_amount=750000, bid_time=now - timedelta(days=5, hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_23", auction_id="auction_10", property_id="prop_8", investor_id="user_13", bid_amount=765000, bid_time=now - timedelta(days=4, hours=8), status=BidStatus.OUTBID),
        Bid(id="bid_24", auction_id="auction_10", property_id="prop_8", investor_id="user_3", bid_amount=785000, bid_time=now - timedelta(days=3, hours=6), status=BidStatus.WINNING),
        
        # Manufacturing Facility - Industrial Investors
        Bid(id="bid_25", auction_id="auction_12", property_id="prop_10", investor_id="user_7", bid_amount=1800000, bid_time=now - timedelta(days=11, hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_26", auction_id="auction_12", property_id="prop_10", investor_id="user_17", bid_amount=1950000, bid_time=now - timedelta(days=10, hours=8), status=BidStatus.OUTBID),
        Bid(id="bid_27", auction_id="auction_12", property_id="prop_10", investor_id="user_7", bid_amount=2150000, bid_time=now - timedelta(days=8, hours=6), status=BidStatus.WINNING),
        
        # Boston Brownstone - Regional Interest
        Bid(id="bid_28", auction_id="auction_14", property_id="prop_13", investor_id="user_8", bid_amount=1850000, bid_time=now - timedelta(days=3, hours=18), status=BidStatus.OUTBID),
        Bid(id="bid_29", auction_id="auction_14", property_id="prop_13", investor_id="user_11", bid_amount=1925000, bid_time=now - timedelta(days=2, hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_30", auction_id="auction_14", property_id="prop_13", investor_id="user_8", bid_amount=2025000, bid_time=now - timedelta(days=1, hours=8), status=BidStatus.WINNING),
        
        # Atlanta Starter Home - First-Time Buyer Competition
        Bid(id="bid_31", auction_id="auction_15", property_id="prop_15", investor_id="user_14", bid_amount=285000, bid_time=now - timedelta(hours=5), status=BidStatus.OUTBID),
        Bid(id="bid_32", auction_id="auction_15", property_id="prop_15", investor_id="user_15", bid_amount=295000, bid_time=now - timedelta(hours=3), status=BidStatus.OUTBID),
        Bid(id="bid_33", auction_id="auction_15", property_id="prop_15", investor_id="user_14", bid_amount=305000, bid_time=now - timedelta(hours=1), status=BidStatus.WINNING),
    ]
    
    # Insert all mock data
    await db.users.insert_many([user.dict() for user in mock_users])
    await db.properties.insert_many([prop.dict() for prop in mock_properties])
    await db.auctions.insert_many([auction.dict() for auction in mock_auctions])
    await db.bids.insert_many([bid.dict() for bid in mock_bids])
    
    logger.info("Enhanced realistic mock data initialized successfully")

# Authentication middleware (dummy for now)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # For now, return a dummy user
    return {"user_id": "demo_user", "email": "demo@example.com", "name": "Demo User"}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Real Estate Auction Analytics API"}

@api_router.post("/auth/login")
async def login(request: LoginRequest):
    # Dummy authentication
    return {"token": "dummy_token", "user": {"id": "demo_user", "email": request.email, "name": "Demo User"}}

@api_router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(100)
    return [User(**user) for user in users]

@api_router.get("/properties", response_model=List[Property])
async def get_properties():
    properties = await db.properties.find().to_list(100)
    return [Property(**prop) for prop in properties]

@api_router.get("/auctions", response_model=List[Auction])
async def get_auctions():
    auctions = await db.auctions.find().to_list(100)
    return [Auction(**auction) for auction in auctions]

@api_router.get("/bids", response_model=List[Bid])
async def get_bids():
    bids = await db.bids.find().to_list(100)
    return [Bid(**bid) for bid in bids]

@api_router.post("/chat", response_model=ChatResponse)
async def chat_query(query: ChatQuery):
    """Enhanced chat endpoint with OpenAI integration"""
    try:
        logger.info(f"Processing query: {query.message}")
        
        # Use OpenAI-powered analytics service
        response = await analytics_service.analyze_query(query.message)
        
        # Store chat message in database
        chat_message = ChatMessage(
            user_id=query.user_id,
            message=query.message,
            response=response.response,
            chart_data=response.chart_data,
            chart_type=response.chart_type,
            summary_points=response.summary_points
        )
        await db.chat_messages.insert_one(chat_message.dict())
        
        logger.info(f"Generated response with chart type: {response.chart_type}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        return ChatResponse(
            response="I apologize, but I encountered an error while processing your request. Please try again with a different question.",
            summary_points=[
                "There was a temporary issue processing your query",
                "Please try rephrasing your question or ask about a different topic"
            ]
        )

@api_router.get("/sample-questions")
async def get_sample_questions():
    return {
        "questions": [
            "Which regions had the highest number of bids last month?",
            "Show upcoming auctions by city in California",
            "Who are the top 5 investors by bid amount?",
            "Compare reserve price vs winning bid for last 10 auctions",
            "What's the bidding activity trend over the past 30 days?",
            "Show me the most active auction categories",
            "Which properties have the highest number of bids?",
            "What's the average success rate by region?"
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_mock_data()
    logger.info("OpenAI-powered analytics service initialized")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()