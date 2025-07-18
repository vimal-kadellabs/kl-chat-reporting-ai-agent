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


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
async def login(email: str, password: str):
    # Dummy authentication
    return {"token": "dummy_token", "user": {"id": "demo_user", "email": email, "name": "Demo User"}}

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
    # For now, return a simple response
    # This will be enhanced with OpenAI integration in Phase 2
    
    message = query.message.lower()
    
    # Simple keyword-based responses for testing
    if "bid" in message and "region" in message:
        # Mock data for regional bidding
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
            response="Here's the bidding activity by region for the last month:",
            chart_data=chart_data,
            chart_type="bar",
            summary_points=[
                "California leads with 45 bids and $2.5M total value",
                "New York follows with 32 bids worth $1.8M",
                "Texas shows strong activity with 28 bids"
            ]
        )
    
    elif "upcoming" in message and "auction" in message:
        # Mock upcoming auctions data
        chart_data = {
            "data": [
                {"city": "San Francisco", "auctions": 3, "total_value": 5200000},
                {"city": "Los Angeles", "auctions": 2, "total_value": 3800000},
                {"city": "New York", "auctions": 4, "total_value": 6100000},
                {"city": "Chicago", "auctions": 1, "total_value": 890000},
                {"city": "Houston", "auctions": 2, "total_value": 2100000}
            ]
        }
        return ChatResponse(
            response="Here are the upcoming auctions by city:",
            chart_data=chart_data,
            chart_type="bar",
            summary_points=[
                "New York has the highest value with $6.1M across 4 auctions",
                "San Francisco follows with $5.2M in 3 auctions",
                "Total of 12 upcoming auctions worth $18.1M"
            ]
        )
    
    elif "investor" in message and "top" in message:
        # Mock top investors data
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
            response="Here are the top 5 investors by bid amount:",
            chart_data=chart_data,
            chart_type="bar",
            summary_points=[
                "Sarah Wilson leads with $4.2M in total bids and 91.2% success rate",
                "Jane Smith follows with $3.8M and 82.3% success rate",
                "Top 5 investors combined: $13.6M in total bid value"
            ]
        )
    
    else:
        return ChatResponse(
            response="I can help you analyze real estate auction data. Try asking about regional bidding, upcoming auctions, or top investors!",
            summary_points=[
                "I'm ready to analyze your real estate auction data",
                "Try asking about bidding trends, regional performance, or investor insights"
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()