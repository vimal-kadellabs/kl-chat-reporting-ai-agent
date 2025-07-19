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
                "cities": list(set([p['city'] for p in properties]))
            }
            return context, {"users": users, "properties": properties, "auctions": auctions, "bids": bids}
        except Exception as e:
            logger.error(f"Error getting database context: {e}")
            return {}, {"users": [], "properties": [], "auctions": [], "bids": []}

    async def analyze_query(self, user_query: str) -> ChatResponse:
        """Use OpenAI to analyze the query and generate appropriate response"""
        try:
            context, raw_data = await self.get_database_context()
            
            # Define function for OpenAI to call
            functions = [
                {
                    "name": "generate_analytics_response",
                    "description": "Generate analytics response with chart data and insights",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response": {
                                "type": "string",
                                "description": "Human-readable response to the user's query"
                            },
                            "chart_type": {
                                "type": "string",
                                "enum": ["bar", "line", "pie", "area", "scatter"],
                                "description": "Most appropriate chart type for the data"
                            },
                            "chart_data": {
                                "type": "object",
                                "description": "Chart data with structure: {data: [{key: value, ...}]}"
                            },
                            "summary_points": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key insights as bullet points (2-4 points)"
                            },
                            "query_type": {
                                "type": "string",
                                "enum": ["regional_analysis", "investor_performance", "auction_trends", "property_analysis", "bidding_patterns", "time_series", "comparison"],
                                "description": "Category of the query"
                            }
                        },
                        "required": ["response", "chart_type", "chart_data", "summary_points", "query_type"]
                    }
                }
            ]

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
1. Appropriate chart visualizations with realistic data
2. Insightful summary points
3. Human-readable responses

Chart Type Guidelines:
- Bar charts: Comparisons between categories (regions, investors, property types)
- Line charts: Trends over time (bidding activity, price changes)
- Pie charts: Proportional data (market share, property type distribution)
- Area charts: Volume over time
- Scatter charts: Correlations between variables

Generate realistic data that matches the query context and current database state.
Make insights actionable and relevant to real estate professionals.
"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                functions=functions,
                function_call={"name": "generate_analytics_response"},
                temperature=0.7
            )

            # Parse the function call response
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "generate_analytics_response":
                result = json.loads(function_call.arguments)
                
                return ChatResponse(
                    response=result["response"],
                    chart_type=result["chart_type"],
                    chart_data=result["chart_data"],
                    summary_points=result["summary_points"]
                )
            else:
                # Fallback if function calling fails
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
    
    # Create mock users
    mock_users = [
        User(id="user_1", email="john.doe@email.com", name="John Doe", location="San Francisco, CA", profile_verified=True, success_rate=75.5, total_bids=25, won_auctions=8),
        User(id="user_2", email="jane.smith@email.com", name="Jane Smith", location="Los Angeles, CA", profile_verified=True, success_rate=82.3, total_bids=30, won_auctions=12),
        User(id="user_3", email="mike.johnson@email.com", name="Mike Johnson", location="New York, NY", profile_verified=True, success_rate=68.9, total_bids=18, won_auctions=5),
        User(id="user_4", email="sarah.wilson@email.com", name="Sarah Wilson", location="Chicago, IL", profile_verified=True, success_rate=91.2, total_bids=35, won_auctions=18),
        User(id="user_5", email="david.brown@email.com", name="David Brown", location="Houston, TX", profile_verified=False, success_rate=45.6, total_bids=12, won_auctions=3),
    ]
    
    # Create mock properties
    mock_properties = [
        Property(id="prop_1", title="Modern Downtown Condo", description="Luxurious 2-bedroom condo in downtown", location="123 Main St, San Francisco, CA", city="San Francisco", state="CA", zipcode="94102", property_type=PropertyType.RESIDENTIAL, reserve_price=750000, estimated_value=850000, bedrooms=2, bathrooms=2, square_feet=1200, year_built=2018),
        Property(id="prop_2", title="Victorian Family Home", description="Classic Victorian home with modern upgrades", location="456 Oak Ave, Los Angeles, CA", city="Los Angeles", state="CA", zipcode="90210", property_type=PropertyType.RESIDENTIAL, reserve_price=1200000, estimated_value=1400000, bedrooms=4, bathrooms=3, square_feet=2800, year_built=1920),
        Property(id="prop_3", title="Commercial Office Building", description="Prime commercial real estate opportunity", location="789 Business Blvd, New York, NY", city="New York", state="NY", zipcode="10001", property_type=PropertyType.COMMERCIAL, reserve_price=2500000, estimated_value=3000000, square_feet=8500, year_built=1985),
        Property(id="prop_4", title="Suburban Ranch House", description="Spacious ranch home with large yard", location="321 Elm St, Chicago, IL", city="Chicago", state="IL", zipcode="60601", property_type=PropertyType.RESIDENTIAL, reserve_price=450000, estimated_value=520000, bedrooms=3, bathrooms=2, square_feet=1800, lot_size=0.3, year_built=1975),
        Property(id="prop_5", title="Industrial Warehouse", description="Large warehouse facility for distribution", location="654 Industrial Dr, Houston, TX", city="Houston", state="TX", zipcode="77001", property_type=PropertyType.INDUSTRIAL, reserve_price=1800000, estimated_value=2200000, square_feet=15000, year_built=1990),
    ]
    
    # Create mock auctions
    now = datetime.utcnow()
    mock_auctions = [
        Auction(id="auction_1", property_id="prop_1", title="Modern Downtown Condo Auction", start_time=now - timedelta(days=2), end_time=now + timedelta(days=1), status=AuctionStatus.LIVE, starting_bid=750000, current_highest_bid=825000, total_bids=15),
        Auction(id="auction_2", property_id="prop_2", title="Victorian Family Home Auction", start_time=now - timedelta(days=7), end_time=now - timedelta(days=1), status=AuctionStatus.ENDED, starting_bid=1200000, current_highest_bid=1350000, total_bids=22, winner_id="user_2"),
        Auction(id="auction_3", property_id="prop_3", title="Commercial Office Building Auction", start_time=now + timedelta(days=3), end_time=now + timedelta(days=10), status=AuctionStatus.UPCOMING, starting_bid=2500000, current_highest_bid=0, total_bids=0),
        Auction(id="auction_4", property_id="prop_4", title="Suburban Ranch House Auction", start_time=now - timedelta(days=5), end_time=now - timedelta(days=2), status=AuctionStatus.ENDED, starting_bid=450000, current_highest_bid=480000, total_bids=8, winner_id="user_4"),
        Auction(id="auction_5", property_id="prop_5", title="Industrial Warehouse Auction", start_time=now + timedelta(days=7), end_time=now + timedelta(days=14), status=AuctionStatus.UPCOMING, starting_bid=1800000, current_highest_bid=0, total_bids=0),
    ]
    
    # Create mock bids
    mock_bids = [
        Bid(id="bid_1", auction_id="auction_1", property_id="prop_1", investor_id="user_1", bid_amount=760000, bid_time=now - timedelta(hours=24), status=BidStatus.OUTBID),
        Bid(id="bid_2", auction_id="auction_1", property_id="prop_1", investor_id="user_2", bid_amount=780000, bid_time=now - timedelta(hours=20), status=BidStatus.OUTBID),
        Bid(id="bid_3", auction_id="auction_1", property_id="prop_1", investor_id="user_3", bid_amount=800000, bid_time=now - timedelta(hours=12), status=BidStatus.OUTBID),
        Bid(id="bid_4", auction_id="auction_1", property_id="prop_1", investor_id="user_4", bid_amount=825000, bid_time=now - timedelta(hours=4), status=BidStatus.WINNING),
        Bid(id="bid_5", auction_id="auction_2", property_id="prop_2", investor_id="user_2", bid_amount=1350000, bid_time=now - timedelta(days=1, hours=2), status=BidStatus.WINNING),
        Bid(id="bid_6", auction_id="auction_4", property_id="prop_4", investor_id="user_4", bid_amount=480000, bid_time=now - timedelta(days=2, hours=1), status=BidStatus.WINNING),
    ]
    
    # Insert mock data
    await db.users.insert_many([user.dict() for user in mock_users])
    await db.properties.insert_many([prop.dict() for prop in mock_properties])
    await db.auctions.insert_many([auction.dict() for auction in mock_auctions])
    await db.bids.insert_many([bid.dict() for bid in mock_bids])
    
    logger.info("Mock data initialized successfully")

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