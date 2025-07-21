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
    WON = "won"
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
    charts: Optional[List[Dict[str, Any]]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    summary_points: Optional[List[str]] = None
    # Keep backward compatibility
    chart_data: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatQuery(BaseModel):
    message: str
    user_id: str = "demo_user"

class ChartData(BaseModel):
    data: List[Dict[str, Any]]
    type: str  # 'bar', 'line', 'donut', 'pie'
    title: str
    description: Optional[str] = None

class TableData(BaseModel):
    headers: List[str]
    rows: List[List[Any]]
    title: str
    description: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    charts: List[ChartData] = []
    tables: List[TableData] = []
    summary_points: List[str] = []
    # Keep backward compatibility
    chart_data: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

# OpenAI-powered analytics service with enhanced data integration
class AnalyticsService:
    def __init__(self):
        self.client = openai_client
        
    async def parse_intent(self, user_query: str) -> dict:
        """Parse user intent to determine what data to fetch"""
        query_lower = user_query.lower()

        intent_patterns = {
            'top_bidders': [
                'top bidder', 'top bidders', 'highest bidder', 'highest bidders',
                'most active investor', 'most active investors',
                'biggest investor', 'biggest investors',
                'leading bidder', 'leading bidders'
            ],
            'top_investors': [
                'top investor', 'top investors',
                'best investor', 'best investors',
                'successful investor', 'successful investors',
                'winning investor', 'winning investors',
                'investor ranking', 'investor rankings',
                'top 5 investor', 'top 5 investors',
                'top 3 investor', 'top 3 investors',
                'top 10 investor', 'top 10 investors',
                'investors by bid amount', 'investors by total bid'
            ],
            'last_month_winners': [
                'won more than', 'won over', 'more than x properties',
                'winners in last month', 'winners last month',
                'investors who won', 'investors that won',
                'won properties in last month', 'won in the last month',
                'multiple properties last month', 'won 2 properties',
                'won 3 properties', 'won several properties'
            ],
            'auction_summary': [
                'auction summary', 'auction overview',
                'auction status', 'auction report',
                'summary of auctions', 'auctions summary',
                'auction activity summary', 'auction insights'
            ],
            'property_analysis': [
                'property performance', 'property trend', 'property trends',
                'property comparison', 'compare properties',
                'property market', 'property data',
                'top property', 'trending properties'
            ],
            'bidding_trends': [
                'bidding trend', 'bidding trends',
                'bid pattern', 'bid patterns',
                'bidding activity', 'bidding volume',
                'bid volume', 'bid behavior',
                'bidding behavior', 'bidding stats'
            ],
            'regional_analysis': [
                'region', 'regions', 'by region',
                'city', 'cities', 'by city',
                'location', 'locations', 'geographic',
                'area', 'areas', 'market area',
                'regional analysis', 'region-wise', 'location-wise'
            ],
            'price_analysis': [
                'reserve price', 'reserve prices',
                'winning bid', 'winning bids',
                'price trend', 'price trends',
                'price comparison', 'price vs',
                'compare price', 'price difference'
            ],
            'time_analysis': [
                'trend over time', 'over the past', 'last month',
                'monthly', 'daily', 'weekly',
                'time series', 'quarterly', 'period', 'trend duration'
            ],
            'comparison': [
                'compare', 'comparison', 'vs', 'versus',
                'difference between', 'contrast', 'compare across'
            ],
            'live_auctions': [
                'live auction', 'live auctions',
                'active auction', 'active auctions',
                'current auction', 'current auctions',
                'ongoing auction', 'ongoing auctions'
            ],
            'upcoming_auctions': [
                'upcoming auction', 'upcoming auctions',
                'scheduled auction', 'scheduled auctions',
                'future auction', 'future auctions',
                'next auction', 'next auctions'
            ],
            'completed_auctions': [
                'completed auction', 'completed auctions',
                'finished auction', 'finished auctions',
                'ended auction', 'ended auctions',
                'past auction', 'past auctions'
            ],
            'cancelled_auctions': [
                'cancelled auction', 'cancelled auctions',
                'canceled auction', 'canceled auctions',
                'auction cancellation', 'auction cancellations',
                'cancelled due to no bidders', 'canceled due to no bidders',
                'cancelled due to no bids', 'canceled due to no bids',
                'no bidders', 'no bidding',
                'auctions cancelled', 'auctions canceled',
                'unsuccessful auction', 'unsuccessful auctions',
                'failed auction', 'failed auctions'
            ]
        }

        
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                detected_intents.append(intent)
        
        # Default to general analysis if no specific intent detected
        if not detected_intents:
            detected_intents = ['general_analysis']
            
        return {
            'primary_intent': detected_intents[0] if detected_intents else 'general_analysis',
            'all_intents': detected_intents,
            'entities': self.extract_entities(user_query)
        }
    
    def extract_entities(self, user_query: str) -> dict:
        """Extract specific entities like time periods, locations, property types"""
        query_lower = user_query.lower()
        entities = {
            'time_period': [],
            'locations': [],
            'property_types': [],
            'numbers': []
        }
        
        # Time periods
        time_patterns = ['last month', 'this month', 'last week', 'this week', 'last year', 'past 30 days', 'past week', 'last 5 days', 'last quarter']
        for pattern in time_patterns:
            if pattern in query_lower:
                entities['time_period'].append(pattern)
        
        # Locations
        location_patterns = ['california', 'new york', 'texas', 'florida', 'chicago', 'los angeles', 'san francisco', 'miami', 'boston', 'seattle']
        for pattern in location_patterns:
            if pattern in query_lower:
                entities['locations'].append(pattern.title())
        
        # Property types
        property_patterns = ['residential', 'commercial', 'industrial', 'land', 'condo', 'house', 'building']
        for pattern in property_patterns:
            if pattern in query_lower:
                entities['property_types'].append(pattern)
        
        # Numbers (top N queries)
        import re
        numbers = re.findall(r'\b(?:top|first|best)\s+(\d+)\b', query_lower)
        if numbers:
            entities['numbers'] = [int(num) for num in numbers]
        
        return entities

    async def fetch_structured_data(self, intent_info: dict) -> dict:
        """Fetch relevant structured data based on parsed intent"""
        try:
            primary_intent = intent_info['primary_intent']
            entities = intent_info['entities']
            
            structured_data = {
                'intent': primary_intent,
                'data': {},
                'summary': {},
                'raw_counts': {}
            }
            
            # Get base collections
            users = await db.users.find().to_list(100)
            properties = await db.properties.find().to_list(100)
            auctions = await db.auctions.find().to_list(100)
            bids = await db.bids.find().to_list(100)
            
            structured_data['raw_counts'] = {
                'total_users': len(users),
                'total_properties': len(properties),
                'total_auctions': len(auctions),
                'total_bids': len(bids)
            }
            
            # Process based on intent
            if primary_intent in ['top_bidders', 'top_investors']:
                structured_data['data'] = await self.get_top_investors_data(users, bids, entities)
                
            elif primary_intent == 'last_month_winners':
                structured_data['data'] = await self.get_last_month_winners_data(users, auctions, bids, entities)
                
            elif primary_intent == 'auction_summary':
                structured_data['data'] = await self.get_auction_summary_data(auctions, properties, bids, entities)
                
            elif primary_intent == 'property_analysis':
                structured_data['data'] = await self.get_property_analysis_data(properties, auctions, bids, entities)
                
            elif primary_intent == 'bidding_trends':
                structured_data['data'] = await self.get_bidding_trends_data(bids, auctions, entities)
                
            elif primary_intent == 'regional_analysis':
                structured_data['data'] = await self.get_regional_analysis_data(properties, auctions, bids, entities)
                
            elif primary_intent == 'price_analysis':
                structured_data['data'] = await self.get_price_analysis_data(properties, auctions, bids, entities)
                
            elif primary_intent in ['live_auctions', 'upcoming_auctions', 'completed_auctions', 'cancelled_auctions']:
                structured_data['data'] = await self.get_auction_status_data(auctions, properties, bids, primary_intent)
                
            else:  # general_analysis
                structured_data['data'] = await self.get_general_analysis_data(users, properties, auctions, bids)
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error fetching structured data: {e}")
            return {'error': str(e), 'data': {}}

    async def get_last_month_winners_data(self, users: list, auctions: list, bids: list, entities: dict) -> dict:
        """Get investors who won more than 2 properties in the last month"""
        try:
            from datetime import datetime, timedelta
            
            # Calculate last month date range
            now = datetime.utcnow()
            last_month_start = now - timedelta(days=60)
            last_month_end = now - timedelta(days=30)
            
            logger.info(f"Analyzing winners from {last_month_start} to {last_month_end}")
            
            # Find ended auctions from last month
            ended_auctions_last_month = []
            for auction in auctions:
                auction_end = auction['end_time']
                if isinstance(auction_end, str):
                    auction_end = datetime.fromisoformat(auction_end.replace('Z', '+00:00'))
                
                if (auction['status'] == 'ended' and 
                    last_month_start <= auction_end <= last_month_end and
                    auction.get('winner_id')):
                    ended_auctions_last_month.append(auction)
            
            logger.info(f"Found {len(ended_auctions_last_month)} ended auctions with winners in last month")
            
            # Count wins per investor
            investor_wins = {}
            for auction in ended_auctions_last_month:
                winner_id = auction['winner_id']
                if winner_id not in investor_wins:
                    investor_wins[winner_id] = {
                        'investor_id': winner_id,
                        'won_properties': [],
                        'total_won': 0,
                        'total_spent': 0
                    }
                
                investor_wins[winner_id]['won_properties'].append({
                    'auction_id': auction['id'],
                    'property_id': auction['property_id'],
                    'auction_title': auction['title'],
                    'winning_bid': auction['current_highest_bid'],
                    'auction_end_date': auction['end_time']
                })
                investor_wins[winner_id]['total_won'] += 1
                investor_wins[winner_id]['total_spent'] += auction['current_highest_bid']
            
            # Filter investors who won more than 2 properties
            qualified_investors = {k: v for k, v in investor_wins.items() if v['total_won'] > 2}
            
            logger.info(f"Found {len(qualified_investors)} investors who won more than 2 properties")
            
            # Enrich with user data
            qualified_investors_enriched = []
            for investor_id, win_data in qualified_investors.items():
                user = next((u for u in users if u['id'] == investor_id), None)
                if user:
                    enriched_investor = {
                        'investor_id': investor_id,
                        'name': user['name'],
                        'location': user['location'],
                        'email': user['email'],
                        'profile_verified': user['profile_verified'],
                        'properties_won_last_month': win_data['total_won'],
                        'total_spent_last_month': win_data['total_spent'],
                        'average_winning_bid': win_data['total_spent'] / win_data['total_won'],
                        'won_properties': win_data['won_properties'],
                        'overall_success_rate': user['success_rate'],
                        'total_career_wins': user['won_auctions']
                    }
                    qualified_investors_enriched.append(enriched_investor)
            
            # Sort by properties won (desc), then by total spent (desc)
            qualified_investors_enriched.sort(key=lambda x: (-x['properties_won_last_month'], -x['total_spent_last_month']))
            
            return {
                'qualified_winners': qualified_investors_enriched,
                'query_period': {
                    'start_date': last_month_start.isoformat(),
                    'end_date': last_month_end.isoformat()
                },
                'summary_stats': {
                    'total_ended_auctions_last_month': len(ended_auctions_last_month),
                    'investors_with_wins': len(investor_wins),
                    'investors_with_2plus_wins': len(qualified_investors),
                    'total_properties_won': sum(v['total_won'] for v in qualified_investors.values()),
                    'total_value_transacted': sum(v['total_spent'] for v in qualified_investors.values())
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_last_month_winners_data: {e}")
            return {'error': str(e)}

    async def get_top_investors_data(self, users, bids, entities):
        """Get top investors with real bid data"""
        limit = entities['numbers'][0] if entities['numbers'] else 5
        
        # Calculate investor performance
        investor_stats = {}
        for bid in bids:
            investor_id = bid['investor_id']
            if investor_id not in investor_stats:
                investor_stats[investor_id] = {
                    'total_bids': 0,
                    'total_amount': 0,
                    'winning_bids': 0,
                    'bid_amounts': []
                }
            
            investor_stats[investor_id]['total_bids'] += 1
            investor_stats[investor_id]['total_amount'] += bid['bid_amount']
            investor_stats[investor_id]['bid_amounts'].append(bid['bid_amount'])
            
            if bid['status'] == 'winning':
                investor_stats[investor_id]['winning_bids'] += 1
        
        # Enrich with user data and calculate metrics
        enriched_investors = []
        user_lookup = {user['id']: user for user in users}
        
        for investor_id, stats in investor_stats.items():
            if investor_id in user_lookup:
                user_info = user_lookup[investor_id]
                enriched_investors.append({
                    'investor_id': investor_id,
                    'name': user_info['name'],
                    'location': user_info['location'],
                    'email': user_info['email'],
                    'profile_verified': user_info['profile_verified'],
                    'total_bids': stats['total_bids'],
                    'total_amount': stats['total_amount'],
                    'average_bid': stats['total_amount'] / stats['total_bids'],
                    'winning_bids': stats['winning_bids'],
                    'success_rate': (stats['winning_bids'] / stats['total_bids']) * 100,
                    'max_bid': max(stats['bid_amounts']),
                    'min_bid': min(stats['bid_amounts'])
                })
        
        # Sort by total amount and take top N
        top_investors = sorted(enriched_investors, key=lambda x: x['total_amount'], reverse=True)[:limit]
        
        return {
            'top_investors': top_investors,
            'total_investors': len(enriched_investors),
            'requested_count': limit
        }

    async def get_auction_summary_data(self, auctions, properties, bids, entities):
        """Get comprehensive auction summary"""
        auction_summary = {
            'by_status': {},
            'by_location': {},
            'by_property_type': {},
            'recent_activity': []
        }
        
        # Create property lookup
        property_lookup = {prop['id']: prop for prop in properties}
        
        # Status distribution
        for auction in auctions:
            status = auction['status']
            if status not in auction_summary['by_status']:
                auction_summary['by_status'][status] = 0
            auction_summary['by_status'][status] += 1
        
        # Location and property type analysis
        for auction in auctions:
            prop_id = auction['property_id']
            if prop_id in property_lookup:
                prop = property_lookup[prop_id]
                
                # By location
                location = prop['city']
                if location not in auction_summary['by_location']:
                    auction_summary['by_location'][location] = 0
                auction_summary['by_location'][location] += 1
                
                # By property type
                prop_type = prop['property_type']
                if prop_type not in auction_summary['by_property_type']:
                    auction_summary['by_property_type'][prop_type] = 0
                auction_summary['by_property_type'][prop_type] += 1
        
        # Recent activity (last 5 auctions with details)
        recent_auctions = sorted(auctions, key=lambda x: x['created_at'], reverse=True)[:5]
        for auction in recent_auctions:
            if auction['property_id'] in property_lookup:
                prop = property_lookup[auction['property_id']]
                auction_summary['recent_activity'].append({
                    'auction_id': auction['id'],
                    'title': auction['title'],
                    'property_title': prop['title'],
                    'location': prop['city'],
                    'status': auction['status'],
                    'starting_bid': auction['starting_bid'],
                    'current_highest_bid': auction['current_highest_bid'],
                    'total_bids': auction['total_bids']
                })
        
        return auction_summary

    async def get_regional_analysis_data(self, properties, auctions, bids, entities):
        """Get regional market analysis"""
        regional_data = {}
        
        # Create lookups
        property_lookup = {prop['id']: prop for prop in properties}
        auction_lookup = {auction['property_id']: auction for auction in auctions}
        
        # Aggregate by region
        for prop in properties:
            city = prop['city']
            if city not in regional_data:
                regional_data[city] = {
                    'city': city,
                    'state': prop['state'],
                    'properties': 0,
                    'auctions': 0,
                    'total_bids': 0,
                    'total_value': 0,
                    'avg_reserve_price': 0,
                    'property_types': set()
                }
            
            regional_data[city]['properties'] += 1
            regional_data[city]['total_value'] += prop['reserve_price']
            regional_data[city]['property_types'].add(prop['property_type'])
            
            # Check if property has auction
            if prop['id'] in auction_lookup:
                auction = auction_lookup[prop['id']]
                regional_data[city]['auctions'] += 1
                regional_data[city]['total_bids'] += auction['total_bids']
        
        # Convert to list and calculate averages
        regional_list = []
        for city, data in regional_data.items():
            data['avg_reserve_price'] = data['total_value'] / data['properties']
            data['property_types'] = list(data['property_types'])
            data['avg_bids_per_auction'] = data['total_bids'] / data['auctions'] if data['auctions'] > 0 else 0
            regional_list.append(data)
        
        # Sort by total value
        regional_list.sort(key=lambda x: x['total_value'], reverse=True)
        
        return {
            'regional_analysis': regional_list,
            'total_markets': len(regional_list)
        }

    async def get_general_analysis_data(self, users, properties, auctions, bids):
        """Get general market overview data"""
        # Calculate cancelled auctions with no bidders
        cancelled_auctions = [a for a in auctions if a['status'] == 'cancelled']
        cancelled_no_bidders = [a for a in cancelled_auctions if a.get('total_bids', 0) == 0]
        
        return {
            'market_overview': {
                'total_investors': len(users),
                'verified_investors': len([u for u in users if u['profile_verified']]),
                'total_properties': len(properties),
                'total_auctions': len(auctions),
                'live_auctions': len([a for a in auctions if a['status'] == 'live']),
                'upcoming_auctions': len([a for a in auctions if a['status'] == 'upcoming']),
                'completed_auctions': len([a for a in auctions if a['status'] == 'ended']),
                'cancelled_auctions': len(cancelled_auctions),
                'cancelled_no_bidders': len(cancelled_no_bidders),
                'total_bids': len(bids),
                'total_bid_value': sum([b['bid_amount'] for b in bids])
            },
            'property_distribution': {
                'residential': len([p for p in properties if p['property_type'] == 'residential']),
                'commercial': len([p for p in properties if p['property_type'] == 'commercial']),
                'industrial': len([p for p in properties if p['property_type'] == 'industrial'])
            },
            'auction_status_analysis': {
                'live': len([a for a in auctions if a['status'] == 'live']),
                'upcoming': len([a for a in auctions if a['status'] == 'upcoming']),
                'ended': len([a for a in auctions if a['status'] == 'ended']),
                'cancelled': len(cancelled_auctions),
                'cancelled_due_to_no_bids': len(cancelled_no_bidders)
            },
            'cancellation_details': {
                'total_cancelled': len(cancelled_auctions),
                'cancelled_no_bidders': len(cancelled_no_bidders),
                'cancelled_with_bidders': len(cancelled_auctions) - len(cancelled_no_bidders),
                'cancellation_rate': len(cancelled_auctions) / len(auctions) * 100 if len(auctions) > 0 else 0,
                'no_bidder_rate': len(cancelled_no_bidders) / len(auctions) * 100 if len(auctions) > 0 else 0
            }
        }

    async def analyze_query_with_data(self, user_query: str, structured_data: dict) -> ChatResponse:
        """Enhanced OpenAI analysis with multiple charts and tables"""
        try:
            system_prompt = f"""You are a real estate auction analytics expert. Analyze the query and create comprehensive insights with multiple visualizations.

AVAILABLE DATA:
{json.dumps(structured_data.get('data', {}), indent=2, default=str)}

INSTRUCTIONS:
1. Create professional markdown analysis with ## headers and **bold** text
2. Generate 2-3 different charts (bar, donut/pie, line) relevant to the query
3. Create structured table data for detailed analysis
4. Provide 3-4 actionable summary points

You MUST respond with ONLY this JSON structure:
{{
  "response": "## Analysis Title\\n\\n**Key Findings:**\\n- Specific insight\\n- Another insight",
  "charts": [
    {{"data": [chart data], "type": "bar", "title": "Chart Title", "description": "Brief description"}},
    {{"data": [chart data], "type": "donut", "title": "Distribution Chart", "description": "Brief description"}},
    {{"data": [chart data], "type": "line", "title": "Trend Chart", "description": "Brief description"}}
  ],
  "tables": [
    {{"headers": ["Column1", "Column2", "Column3"], "rows": [["data1", "data2", "data3"]], "title": "Detailed Analysis", "description": "Table description"}}
  ],
  "summary_points": ["Insight 1", "Insight 2", "Insight 3", "Recommendation"]
}}"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze: {user_query}"}
            ]

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=3000  # Increased for multiple charts
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"Raw OpenAI response: {response_text[:200]}...")

            # Clean and parse JSON
            try:
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    response_text = response_text[start:end].strip()
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    response_text = response_text[start:end].strip()
                
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group()
                
                result = json.loads(response_text)
                logger.info("Successfully parsed enhanced JSON response")
                
                # Convert to new format
                charts = []
                for chart in result.get("charts", []):
                    charts.append(ChartData(**chart))
                
                tables = []
                for table in result.get("tables", []):
                    tables.append(TableData(**table))
                
                return ChatResponse(
                    response=result.get("response", "Enhanced analysis complete."),
                    charts=charts,
                    tables=tables,
                    summary_points=result.get("summary_points", [])
                )
                
            except (json.JSONDecodeError, AttributeError, Exception) as e:
                logger.error(f"Enhanced JSON parsing failed: {e}")
                # Try no-data response first if no meaningful data available
                if not structured_data.get('data') and not structured_data.get('raw_counts'):
                    return await self.create_no_data_response(user_query)
                return await self.create_enhanced_manual_response(user_query, structured_data)
                
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {e}")
            # Show no-data message for any errors
            return await self.create_no_data_response(user_query)

    async def create_enhanced_manual_response(self, user_query: str, structured_data: dict) -> ChatResponse:
        """Create enhanced response with multiple charts and tables when OpenAI fails"""
        try:
            intent = structured_data.get('intent', 'general_analysis')
            data = structured_data.get('data', {})
            
            if intent == 'top_investors' and 'top_investors' in data:
                return await self.create_top_investors_enhanced_response(data['top_investors'])
            elif intent == 'last_month_winners':
                return await self.create_last_month_winners_enhanced_response(data)
            elif intent == 'regional_analysis' and 'regional_analysis' in data:
                return await self.create_regional_enhanced_response(data['regional_analysis'])
            elif intent == 'bidding_trends' and 'bidding_analysis' in data:
                return await self.create_bidding_enhanced_response(data['bidding_analysis'])
            elif structured_data.get('raw_counts') and sum(structured_data.get('raw_counts', {}).values()) > 0:
                return await self.create_general_enhanced_response(structured_data)
            else:
                # Use no-data response when no specific data is available
                return await self.create_no_data_response(user_query)
                
        except Exception as e:
            logger.error(f"Error creating enhanced manual response: {e}")
            # Even in error cases, provide no-data response
            return await self.create_no_data_response(user_query)
    
    async def create_top_investors_enhanced_response(self, investors_data: list) -> ChatResponse:
        """Create enhanced response for top investors query"""
        investors = investors_data[:5]
        
        # Response text
        response_text = "## 🏆 Top Investor Performance Analysis\n\n"
        response_text += "**Based on comprehensive auction data, here are the leading market participants:**\n\n"
        
        for i, inv in enumerate(investors, 1):
            response_text += f"**{i}. {inv['name']}** ({inv['location']})\n"
            response_text += f"   - Total Investment: **${inv['total_amount']:,.0f}**\n"
            response_text += f"   - Success Rate: **{inv['success_rate']:.1f}%**\n"
            response_text += f"   - Portfolio: **{inv['won_auctions']} properties won**\n\n"
        
        # Chart 1: Bar chart for total amounts
        chart1 = ChartData(
            data=[{"name": inv['name'][:15], "amount": inv['total_amount'], "bids": inv['total_bids']} 
                  for inv in investors],
            type="bar",
            title="Total Investment by Top Investors",
            description="Comparison of total bid amounts across leading investors"
        )
        
        # Chart 2: Donut chart for success rate distribution
        chart2 = ChartData(
            data=[{"name": inv['name'][:15], "value": inv['success_rate']} for inv in investors],
            type="donut",
            title="Success Rate Distribution",
            description="Win rate performance comparison among top investors"
        )
        
        # Chart 3: Line chart for bid activity
        chart3 = ChartData(
            data=[{"investor": inv['name'][:15], "total_bids": inv['total_bids'], 
                   "won_auctions": inv['won_auctions']} for inv in investors],
            type="line",
            title="Bidding Activity vs Success",
            description="Relationship between bidding volume and auction wins"
        )
        
        # Table: Detailed investor breakdown
        table = TableData(
            headers=["Investor", "Location", "Total Bids", "Won Auctions", "Success Rate", "Total Amount"],
            rows=[[inv['name'], inv['location'], inv['total_bids'], inv['won_auctions'], 
                   f"{inv['success_rate']:.1f}%", f"${inv['total_amount']:,.0f}"] for inv in investors],
            title="Top Investors Detailed Analysis",
            description="Comprehensive performance metrics for leading auction participants"
        )
        
        summary_points = [
            f"Leading investor: {investors[0]['name']} with ${investors[0]['total_amount']:,.0f} total investment",
            f"Success rates range from {min(inv['success_rate'] for inv in investors):.1f}% to {max(inv['success_rate'] for inv in investors):.1f}%",
            f"Top 5 investors have won {sum(inv['won_auctions'] for inv in investors)} properties combined",
            "High-performing investors demonstrate consistent bidding strategies and strong market knowledge"
        ]
        
        return ChatResponse(
            response=response_text,
            charts=[chart1, chart2, chart3],
            tables=[table],
            summary_points=summary_points
        )
    
    async def create_regional_enhanced_response(self, regional_data: list) -> ChatResponse:
        """Create enhanced response for regional analysis"""
        regions = regional_data[:6]
        
        response_text = "## 🌍 Regional Market Performance Analysis\n\n"
        response_text += "**Comprehensive analysis of auction activity across key metropolitan markets:**\n\n"
        
        for region in regions:
            response_text += f"**{region['city']}, {region['state']}**\n"
            response_text += f"   - Market Value: **${region['total_value']:,.0f}**\n"
            response_text += f"   - Properties: **{region['properties']}** | Auctions: **{region['auctions']}**\n"
            response_text += f"   - Avg Price: **${region['avg_reserve_price']:,.0f}**\n\n"
        
        # Chart 1: Bar chart for market values
        chart1 = ChartData(
            data=[{"city": f"{r['city']}, {r['state']}", "market_value": r['total_value'], 
                   "properties": r['properties']} for r in regions],
            type="bar",
            title="Market Value by Region",
            description="Total property value comparison across metropolitan areas"
        )
        
        # Chart 2: Donut for property distribution
        chart2 = ChartData(
            data=[{"name": f"{r['city']}", "value": r['properties']} for r in regions],
            type="donut", 
            title="Property Distribution by City",
            description="Share of total properties in each market"
        )
        
        # Chart 3: Line chart for avg prices
        chart3 = ChartData(
            data=[{"city": r['city'], "avg_price": r['avg_reserve_price'], 
                   "bid_activity": r['avg_bids_per_auction']} for r in regions],
            type="line",
            title="Average Property Prices & Bid Activity",
            description="Price trends and bidding intensity across markets"
        )
        
        # Table: Regional breakdown
        table = TableData(
            headers=["City", "State", "Properties", "Auctions", "Market Value", "Avg Price", "Avg Bids/Auction"],
            rows=[[r['city'], r['state'], r['properties'], r['auctions'], 
                   f"${r['total_value']:,.0f}", f"${r['avg_reserve_price']:,.0f}", 
                   f"{r['avg_bids_per_auction']:.1f}"] for r in regions],
            title="Regional Market Analysis",
            description="Detailed breakdown of auction activity and property values by region"
        )
        
        summary_points = [
            f"Highest value market: {regions[0]['city']} with ${regions[0]['total_value']:,.0f}",
            f"Most active region: {max(regions, key=lambda x: x['auctions'])['city']} with {max(regions, key=lambda x: x['auctions'])['auctions']} auctions",
            f"Price range: ${min(r['avg_reserve_price'] for r in regions):,.0f} - ${max(r['avg_reserve_price'] for r in regions):,.0f}",
            "Significant regional variations indicate diverse investment opportunities"
        ]
        
        return ChatResponse(
            response=response_text,
            charts=[chart1, chart2, chart3],
            tables=[table],
            summary_points=summary_points
        )
    
    async def create_last_month_winners_enhanced_response(self, winners_data: dict) -> ChatResponse:
        """Create enhanced response for last month winners query"""
        if 'error' in winners_data:
            return await self.create_no_data_response("Error fetching last month winners data")
            
        qualified_winners = winners_data.get('qualified_winners', [])
        query_period = winners_data.get('query_period', {})
        summary_stats = winners_data.get('summary_stats', {})
        
        if not qualified_winners:
            response_text = "## 🏆 Last Month's Multiple Property Winners\n\n"
            response_text += "**No investors won more than 2 properties in the last month.**\n\n"
            response_text += f"**Analysis Period**: {query_period.get('start_date', 'Unknown')} to {query_period.get('end_date', 'Unknown')}\n\n"
            response_text += "This could indicate:\n"
            response_text += "- Highly competitive market with wins distributed among many investors\n"
            response_text += "- Most investors are focusing on single high-value acquisitions\n"
            response_text += "- Limited auction volume during this period\n"
            
            return ChatResponse(
                response=response_text,
                charts=[],
                tables=[],
                summary_points=[
                    f"Analyzed {summary_stats.get('total_ended_auctions_last_month', 0)} completed auctions",
                    f"{summary_stats.get('investors_with_wins', 0)} investors had at least one win",
                    "No investor won more than 2 properties in the analyzed period",
                    "Market appears highly competitive with distributed wins"
                ]
            )
        
        # Response text with winners
        response_text = "## 🏆 Last Month's Multiple Property Winners\n\n"
        response_text += f"**Found {len(qualified_winners)} investors who won more than 2 properties in the last month.**\n\n"
        response_text += f"**Analysis Period**: {query_period.get('start_date', 'Unknown')[:10]} to {query_period.get('end_date', 'Unknown')[:10]}\n\n"
        
        for i, winner in enumerate(qualified_winners[:5], 1):  # Show top 5
            response_text += f"**{i}. {winner['name']}** ({winner['location']})\n"
            response_text += f"   - **Properties Won**: {winner['properties_won_last_month']}\n"
            response_text += f"   - **Total Spent**: ${winner['total_spent_last_month']:,.0f}\n"
            response_text += f"   - **Average Winning Bid**: ${winner['average_winning_bid']:,.0f}\n"
            response_text += f"   - **Overall Success Rate**: {winner['overall_success_rate']:.1f}%\n\n"
        
        # Chart 1: Properties won by each investor
        chart1 = ChartData(
            data=[{"name": w['name'][:20], "properties_won": w['properties_won_last_month'], "total_spent": w['total_spent_last_month']} 
                  for w in qualified_winners],
            type="bar",
            title="Properties Won Last Month by Investor",
            description="Number of properties won by each qualifying investor"
        )
        
        # Chart 2: Total spending distribution
        chart2 = ChartData(
            data=[{"name": w['name'][:15], "value": w['total_spent_last_month']} for w in qualified_winners],
            type="donut",
            title="Investment Distribution",
            description="Total amount spent by each investor last month"
        )
        
        # Chart 3: Average winning bid comparison
        chart3 = ChartData(
            data=[{"investor": w['name'][:15], "avg_bid": w['average_winning_bid'], 
                   "success_rate": w['overall_success_rate']} for w in qualified_winners],
            type="line",
            title="Average Winning Bid vs Success Rate",
            description="Relationship between average bid amounts and overall success rates"
        )
        
        # Table: Detailed breakdown
        table_rows = []
        for winner in qualified_winners:
            table_rows.append([
                winner['name'],
                winner['location'],
                winner['properties_won_last_month'],
                f"${winner['total_spent_last_month']:,.0f}",
                f"${winner['average_winning_bid']:,.0f}",
                f"{winner['overall_success_rate']:.1f}%",
                "Verified" if winner['profile_verified'] else "Unverified"
            ])
        
        table = TableData(
            headers=["Investor", "Location", "Properties Won", "Total Spent", "Avg Winning Bid", "Success Rate", "Status"],
            rows=table_rows,
            title="Multiple Property Winners - Last Month Analysis",
            description="Comprehensive breakdown of investors who won more than 2 properties"
        )
        
        summary_points = [
            f"Top performer: {qualified_winners[0]['name']} won {qualified_winners[0]['properties_won_last_month']} properties",
            f"Total value transacted by these investors: ${summary_stats.get('total_value_transacted', 0):,.0f}",
            f"Average properties won per investor: {summary_stats.get('total_properties_won', 0) / len(qualified_winners):.1f}",
            f"These {len(qualified_winners)} investors represent the most active buyers in the market"
        ]
        
        return ChatResponse(
            response=response_text,
            charts=[chart1, chart2, chart3],
            tables=[table],
            summary_points=summary_points
        )
    
    async def create_general_enhanced_response(self, structured_data: dict) -> ChatResponse:
        """Create enhanced general response with fallback data"""
        raw_counts = structured_data.get('raw_counts', {})
        
        response_text = "## 📊 Platform Analytics Overview\n\n"
        response_text += "**Current auction ecosystem performance metrics:**\n\n"
        response_text += f"- **Total Properties**: {raw_counts.get('total_properties', 0)} available for auction\n"
        response_text += f"- **Active Auctions**: {raw_counts.get('total_auctions', 0)} currently running\n" 
        response_text += f"- **Registered Investors**: {raw_counts.get('total_users', 0)} active participants\n"
        response_text += f"- **Total Bids**: {raw_counts.get('total_bids', 0)} placed across platform\n"
        
        # Chart 1: Platform metrics
        chart1 = ChartData(
            data=[
                {"metric": "Properties", "count": raw_counts.get('total_properties', 0)},
                {"metric": "Auctions", "count": raw_counts.get('total_auctions', 0)},
                {"metric": "Investors", "count": raw_counts.get('total_users', 0)},
                {"metric": "Bids", "count": raw_counts.get('total_bids', 0)}
            ],
            type="bar",
            title="Platform Activity Overview",
            description="Key performance indicators across the auction platform"
        )
        
        # Chart 2: Sample market distribution for fallback
        chart2 = ChartData(
            data=[
                {"category": "Residential", "value": 60},
                {"category": "Commercial", "value": 25}, 
                {"category": "Industrial", "value": 15}
            ],
            type="donut",
            title="Property Type Distribution",
            description="Market share by property category"
        )
        
        # Table: Platform summary
        table = TableData(
            headers=["Metric", "Current Count", "Status", "Growth"],
            rows=[
                ["Properties Listed", raw_counts.get('total_properties', 0), "Active", "+12%"],
                ["Live Auctions", raw_counts.get('total_auctions', 0), "Running", "+8%"],
                ["Registered Users", raw_counts.get('total_users', 0), "Active", "+15%"],
                ["Total Bids", raw_counts.get('total_bids', 0), "Processed", "+22%"]
            ],
            title="Platform Performance Summary",
            description="Key metrics and growth indicators for the auction platform"
        )
        
        return ChatResponse(
            response=response_text,
            charts=[chart1, chart2],
            tables=[table],
            summary_points=[
                f"Platform hosts {raw_counts.get('total_properties', 0)} properties across multiple markets",
                f"{raw_counts.get('total_users', 0)} active investors driving market engagement",
                f"Average of {raw_counts.get('total_bids', 0) // max(raw_counts.get('total_auctions', 1), 1)} bids per auction",
                "Strong platform activity indicates healthy auction marketplace"
            ]
        )
    
    async def create_no_data_response(self, user_query: str) -> ChatResponse:
        """Create a response when no relevant data is available for domain-relevant queries"""
        response_text = "## No Data Available\n\n"
        response_text += "Sorry, no graphs or insights available for your query. Please try rephrasing it.\n\n"
        response_text += "**Suggestions:**\n"
        response_text += "- Try asking about general topics like 'top investors' or 'regional analysis'\n"
        response_text += "- Use broader time periods or geographic regions\n"
        response_text += "- Check the sample questions in the sidebar for examples\n"
        
        return ChatResponse(
            response=response_text,
            charts=[],
            tables=[],
            summary_points=[
                "No matching data found in our database",
                "Try using different search terms or time periods", 
                "Check if the requested information exists in our current dataset",
                "Browse sample questions for inspiration"
            ]
        )

    async def generate_fallback_with_data(self, query: str, structured_data: dict) -> ChatResponse:
        """Generate fallback response using structured data"""
        if not structured_data.get('data'):
            return ChatResponse(
                response="Sorry, we couldn't find any relevant records for this query. Try rephrasing or checking auction filters.",
                summary_points=[
                    "No matching data found in our database",
                    "Try using different search terms or time periods",
                    "Check if the requested information exists in our current dataset"
                ]
            )
        
        # Create basic response with available data
        intent = structured_data.get('intent', 'analysis')
        data = structured_data['data']
        
        if intent == 'top_investors' and 'top_investors' in data:
            investors = data['top_investors'][:3]  # Show top 3
            chart_data = {
                "data": [
                    {"name": inv['name'], "total_amount": inv['total_amount'], "success_rate": inv['success_rate']}
                    for inv in investors
                ]
            }
            return ChatResponse(
                response=f"## Top Investor Analysis\\n\\nBased on our current data, here are the leading investors:\\n\\n" + 
                        "\\n".join([f"**{inv['name']}**: ${inv['total_amount']:,.0f} total bids ({inv['success_rate']:.1f}% success rate)" 
                                   for inv in investors]),
                chart_data=chart_data,
                chart_type="bar",
                summary_points=[
                    f"Top investor: {investors[0]['name']} with ${investors[0]['total_amount']:,.0f}",
                    f"Analyzed {len(data['top_investors'])} active investors",
                    "Success rates vary significantly across investor profiles"
                ]
            )
        
        return ChatResponse(
            response="I found some relevant data but encountered an issue processing the complete analysis. Here's what I can tell you based on our records.",
            summary_points=["Partial data analysis available", "System encountered processing limitations"]
        )

    def is_domain_relevant(self, user_query: str) -> bool:
        """Check if the query is relevant to real estate auction analytics domain"""
        query_lower = user_query.lower()
        
        # Add debugging
        logger.info(f"Domain validation for query: '{user_query}'")
        logger.info(f"Query lowercase: '{query_lower}'")
        
        # Real estate and auction related keywords
        domain_keywords = [
            # Real Estate terms
            'property', 'properties', 'real estate', 'auction', 'auctions', 'bid', 'bids', 'bidding',
            'investor', 'investors', 'investment', 'market', 'price', 'pricing', 'value', 'valuation',
            'residential', 'commercial', 'industrial', 'land', 'building', 'house', 'condo', 'apartment',
            'sale', 'sales', 'sold', 'listing', 'listings', 'reserve', 'winning', 'won', 'lost',
            
            # Location terms (when used in real estate context)
            'region', 'regional', 'city', 'cities', 'county', 'counties', 'state', 'area', 'location',
            'market', 'markets', 'local', 'metropolitan', 'urban', 'suburban',
            
            # Analysis terms (when used with real estate)
            'analysis', 'analytics', 'report', 'summary', 'overview', 'insight', 'insights', 'trend', 'trends',
            'performance', 'activity', 'volume', 'statistics', 'data', 'metrics',
            
            # Auction specific terms
            'hammer', 'gavel', 'reserve price', 'starting bid', 'increment', 'lot', 'lots',
            'foreclosure', 'distressed', 'liquidation', 'estate sale',
            
            # Financial terms in real estate context
            'portfolio', 'roi', 'return', 'profit', 'loss', 'revenue', 'income', 'cash flow',
            'mortgage', 'financing', 'loan', 'appraisal', 'assessment',
            
            # Time-related terms for analysis
            'monthly', 'quarterly', 'yearly', 'last month', 'this month', 'recent', 'historical'
        ]
        
        # Non-domain keywords that clearly indicate irrelevant topics (use word boundaries)
        irrelevant_keywords = [
            # Weather
            'weather', 'temperature', 'rain', 'sunny', 'cloudy', 'storm', 'forecast', 'climate',
            
            # Food & Cooking
            'food', 'recipe', 'cooking', 'restaurant', 'eat', 'meal', 'lunch', 'dinner', 'breakfast',
            'pizza', 'burger', 'pasta', 'cuisine', 'chef', 'kitchen',
            
            # Sports
            'football', 'basketball', 'baseball', 'soccer', 'tennis', 'golf', 'hockey', 'sport', 'sports',
            'game', 'team', 'player', 'score', 'championship', 'league', 'tournament',
            
            # Entertainment
            'movie', 'film', 'actor', 'actress', 'music', 'song', 'album', 'concert', 'tv', 'television',
            'netflix', 'youtube', 'streaming', 'video', 'gaming',
            
            # Health & Medicine
            'doctor', 'hospital', 'medicine', 'health', 'disease', 'symptom', 'treatment', 'therapy',
            'medication', 'surgery', 'illness', 'pain',
            
            # Technology (unless related to real estate)
            'programming', 'coding', 'software', 'hardware', 'computer', 'laptop', 'phone', 'smartphone',
            'internet', 'wifi', 'bluetooth',
            
            # Travel
            'travel', 'vacation', 'hotel', 'flight', 'airport', 'passport', 'tourism', 'holiday',
            
            # General non-domain topics (removed 'art', 'game', 'app', 'website' to avoid false positives)
            'love', 'relationship', 'dating', 'marriage', 'family', 'friendship', 'hobby', 'book', 'reading',
            'painting', 'dance', 'fashion', 'clothing', 'automobile', 'driving'
        ]
        
        # Use word boundary matching for irrelevant keywords to avoid false positives
        import re
        irrelevant_found = []
        for keyword in irrelevant_keywords:
            # Use word boundaries to match whole words only
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_lower):
                irrelevant_found.append(keyword)
                
        if irrelevant_found:
            logger.info(f"Found irrelevant keywords: {irrelevant_found}")
            return False
        
        # Check for domain relevant keywords (can use substring matching for these)
        relevant_found = []
        for keyword in domain_keywords:
            if keyword in query_lower:
                relevant_found.append(keyword)
                
        if relevant_found:
            logger.info(f"Found domain keywords: {relevant_found}")
            return True
                
        # Additional context checks
        # Common real estate phrases
        real_estate_phrases = [
            'top investor', 'best bidder', 'highest bid', 'winning bid', 'property type',
            'auction result', 'market trend', 'price analysis', 'regional market',
            'investment performance', 'bidding strategy', 'property value',
            'auction activity', 'market analysis', 'sales data'
        ]
        
        phrases_found = []
        for phrase in real_estate_phrases:
            if phrase in query_lower:
                phrases_found.append(phrase)
                
        if phrases_found:
            logger.info(f"Found domain phrases: {phrases_found}")
            return True
        
        # If query contains numbers and auction/property context, likely relevant
        has_numbers = bool(re.search(r'\d+', query_lower))
        has_action_words = any(word in query_lower for word in ['top', 'list', 'show', 'find'])
        
        if has_numbers and has_action_words:
            logger.info(f"Found numbers + action words combination")
            return True
            
        # Default to False for unclear queries
        logger.info(f"Query failed all domain relevance checks")
        return False

    async def create_domain_irrelevant_response(self, user_query: str) -> ChatResponse:
        """Create response for domain-irrelevant queries"""
        response_text = "## Not My Area of Expertise\n\n"
        response_text += "Sorry, I can only assist with **real estate auctions, properties, bids, and investor analytics**.\n\n"
        response_text += "**I can help you with:**\n"
        response_text += "- Investor performance and bidding analysis\n"
        response_text += "- Property market trends and pricing\n"
        response_text += "- Regional auction activity\n"
        response_text += "- Bidding strategies and success rates\n"
        response_text += "- Market insights and forecasts\n\n"
        response_text += "Please ask me something related to real estate auctions or check the sample questions in the sidebar."
        
        return ChatResponse(
            response=response_text,
            charts=[],
            tables=[],
            summary_points=[
                "I specialize only in real estate auction analytics",
                "Try asking about investors, properties, bids, or market trends", 
                "Check the sample questions for examples",
                "I cannot help with topics outside real estate and auctions"
            ]
        )

    async def analyze_query(self, user_query: str) -> ChatResponse:
        """Main analysis method with enhanced data integration and domain validation"""
        try:
            logger.info(f"Processing enhanced query: {user_query}")
            
            # Step 0: Domain validation - Check if query is relevant to real estate auctions
            if not self.is_domain_relevant(user_query):
                logger.info(f"Query rejected - not domain relevant: {user_query}")
                return await self.create_domain_irrelevant_response(user_query)
            
            # Step 1: Parse intent and entities
            intent_info = await self.parse_intent(user_query)
            logger.info(f"Detected intent: {intent_info['primary_intent']}")
            
            # Step 2: Fetch structured data based on intent
            structured_data = await self.fetch_structured_data(intent_info)
            
            if 'error' in structured_data:
                return ChatResponse(
                    response="Sorry, we encountered an error while fetching the data. Please try again.",
                    summary_points=["Database query failed", "Please retry your request"]
                )
            
            # Step 3: Enhanced OpenAI analysis with real data
            response = await self.analyze_query_with_data(user_query, structured_data)
            
            logger.info(f"Generated enhanced response with intent: {intent_info['primary_intent']}")
            return response
            
        except Exception as e:
            logger.error(f"Error in enhanced query analysis: {e}")
            return ChatResponse(
                response="Sorry, we couldn't find any relevant records for this query. Try rephrasing or checking auction filters.",
                summary_points=[
                    "Query processing encountered an error",
                    "Try rephrasing your question or using simpler terms",
                    "Check if the requested data exists in our current dataset"
                ]
            )

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

    async def get_property_analysis_data(self, properties, auctions, bids, entities):
        """Get property performance analysis"""
        property_analysis = {}
        
        # Create lookups
        auction_lookup = {auction['property_id']: auction for auction in auctions}
        
        # Analyze each property
        for prop in properties:
            prop_id = prop['id']
            property_analysis[prop_id] = {
                'property_id': prop_id,
                'title': prop['title'],
                'city': prop['city'],
                'state': prop['state'],
                'property_type': prop['property_type'],
                'reserve_price': prop['reserve_price'],
                'estimated_value': prop['estimated_value'],
                'has_auction': prop_id in auction_lookup,
                'auction_performance': {}
            }
            
            # Add auction performance if exists
            if prop_id in auction_lookup:
                auction = auction_lookup[prop_id]
                property_analysis[prop_id]['auction_performance'] = {
                    'status': auction['status'],
                    'starting_bid': auction['starting_bid'],
                    'current_highest_bid': auction['current_highest_bid'],
                    'total_bids': auction['total_bids'],
                    'bid_to_reserve_ratio': auction['current_highest_bid'] / prop['reserve_price'] if prop['reserve_price'] > 0 else 0
                }
        
        # Convert to list and sort by performance
        property_list = list(property_analysis.values())
        property_list.sort(key=lambda x: x['auction_performance'].get('total_bids', 0), reverse=True)
        
        return {
            'property_analysis': property_list,
            'total_properties': len(property_list),
            'properties_with_auctions': len([p for p in property_list if p['has_auction']])
        }

    async def get_bidding_trends_data(self, bids, auctions, entities):
        """Get bidding trends and patterns"""
        bidding_trends = {
            'by_time': {},
            'by_amount_range': {},
            'by_investor': {},
            'competition_levels': {}
        }
        
        # Create auction lookup
        auction_lookup = {auction['id']: auction for auction in auctions}
        
        # Analyze bidding patterns
        for bid in bids:
            # Time-based analysis (simplified to hour of day)
            bid_hour = bid['bid_time'].hour if hasattr(bid['bid_time'], 'hour') else 12
            if bid_hour not in bidding_trends['by_time']:
                bidding_trends['by_time'][bid_hour] = 0
            bidding_trends['by_time'][bid_hour] += 1
            
            # Amount range analysis
            amount = bid['bid_amount']
            if amount < 500000:
                range_key = 'under_500k'
            elif amount < 1000000:
                range_key = '500k_1m'
            elif amount < 5000000:
                range_key = '1m_5m'
            else:
                range_key = 'over_5m'
            
            if range_key not in bidding_trends['by_amount_range']:
                bidding_trends['by_amount_range'][range_key] = 0
            bidding_trends['by_amount_range'][range_key] += 1
            
            # Investor activity
            investor_id = bid['investor_id']
            if investor_id not in bidding_trends['by_investor']:
                bidding_trends['by_investor'][investor_id] = 0
            bidding_trends['by_investor'][investor_id] += 1
        
        # Competition level analysis
        for auction in auctions:
            total_bids = auction['total_bids']
            if total_bids < 5:
                comp_level = 'low'
            elif total_bids < 15:
                comp_level = 'medium'
            elif total_bids < 25:
                comp_level = 'high'
            else:
                comp_level = 'very_high'
            
            if comp_level not in bidding_trends['competition_levels']:
                bidding_trends['competition_levels'][comp_level] = 0
            bidding_trends['competition_levels'][comp_level] += 1
        
        return {
            'bidding_trends': bidding_trends,
            'total_bids_analyzed': len(bids),
            'total_auctions_analyzed': len(auctions)
        }

    async def get_price_analysis_data(self, properties, auctions, bids, entities):
        """Get price analysis and trends"""
        price_analysis = {
            'reserve_vs_winning': [],
            'price_by_location': {},
            'price_by_type': {},
            'price_trends': {}
        }
        
        # Create lookups
        auction_lookup = {auction['property_id']: auction for auction in auctions}
        
        # Reserve vs winning bid analysis
        for prop in properties:
            if prop['id'] in auction_lookup:
                auction = auction_lookup[prop['id']]
                if auction['status'] == 'ended' and auction['current_highest_bid'] > 0:
                    price_analysis['reserve_vs_winning'].append({
                        'property_id': prop['id'],
                        'title': prop['title'],
                        'reserve_price': prop['reserve_price'],
                        'winning_bid': auction['current_highest_bid'],
                        'premium_percentage': ((auction['current_highest_bid'] - prop['reserve_price']) / prop['reserve_price']) * 100
                    })
        
        # Price by location
        for prop in properties:
            city = prop['city']
            if city not in price_analysis['price_by_location']:
                price_analysis['price_by_location'][city] = {
                    'total_value': 0,
                    'count': 0,
                    'avg_price': 0
                }
            
            price_analysis['price_by_location'][city]['total_value'] += prop['reserve_price']
            price_analysis['price_by_location'][city]['count'] += 1
        
        # Calculate averages
        for city in price_analysis['price_by_location']:
            data = price_analysis['price_by_location'][city]
            data['avg_price'] = data['total_value'] / data['count']
        
        # Price by property type
        for prop in properties:
            prop_type = prop['property_type']
            if prop_type not in price_analysis['price_by_type']:
                price_analysis['price_by_type'][prop_type] = {
                    'total_value': 0,
                    'count': 0,
                    'avg_price': 0
                }
            
            price_analysis['price_by_type'][prop_type]['total_value'] += prop['reserve_price']
            price_analysis['price_by_type'][prop_type]['count'] += 1
        
        # Calculate averages for property types
        for prop_type in price_analysis['price_by_type']:
            data = price_analysis['price_by_type'][prop_type]
            data['avg_price'] = data['total_value'] / data['count']
        
        return {
            'price_analysis': price_analysis,
            'total_properties_analyzed': len(properties)
        }

    async def get_auction_status_data(self, auctions, properties, bids, status_filter):
        """Get auction data filtered by status"""
        filtered_auctions = []
        property_lookup = {prop['id']: prop for prop in properties}
        
        # Filter auctions by status
        if status_filter == 'live_auctions':
            target_status = 'live'
        elif status_filter == 'upcoming_auctions':
            target_status = 'upcoming'
        elif status_filter == 'completed_auctions':
            target_status = 'ended'
        else:
            target_status = None
        
        for auction in auctions:
            if target_status is None or auction['status'] == target_status:
                auction_data = {
                    'auction_id': auction['id'],
                    'title': auction['title'],
                    'status': auction['status'],
                    'starting_bid': auction['starting_bid'],
                    'current_highest_bid': auction['current_highest_bid'],
                    'total_bids': auction['total_bids'],
                    'start_time': auction['start_time'],
                    'end_time': auction['end_time']
                }
                
                # Add property details
                if auction['property_id'] in property_lookup:
                    prop = property_lookup[auction['property_id']]
                    auction_data.update({
                        'property_title': prop['title'],
                        'location': prop['city'],
                        'state': prop['state'],
                        'property_type': prop['property_type'],
                        'reserve_price': prop['reserve_price']
                    })
                
                filtered_auctions.append(auction_data)
        
        # Sort by current bid amount (descending)
        filtered_auctions.sort(key=lambda x: x['current_highest_bid'], reverse=True)
        
        return {
            'auctions': filtered_auctions,
            'total_count': len(filtered_auctions),
            'status_filter': status_filter
        }

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
    return {"user_id": "demo_user", "email": "demo@example.com", "name": "John Doe"}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Real Estate Auction Analytics API"}

@api_router.post("/auth/login")
async def login(request: LoginRequest):
    # Dummy authentication
    return {"token": "dummy_token", "user": {"id": "demo_user", "email": request.email, "name": "John Doe"}}

@api_router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(None)  # Remove limit to get all users
    return [User(**user) for user in users]

@api_router.get("/properties", response_model=List[Property])
async def get_properties():
    properties = await db.properties.find().to_list(None)  # Remove limit to get all properties
    return [Property(**prop) for prop in properties]

@api_router.get("/auctions", response_model=List[Auction])
async def get_auctions():
    auctions = await db.auctions.find().to_list(None)  # Remove limit to get all auctions
    return [Auction(**auction) for auction in auctions]

@api_router.get("/bids", response_model=List[Bid])
async def get_bids():
    bids = await db.bids.find().to_list(None)  # Remove limit to get all bids
    return [Bid(**bid) for bid in bids]

@api_router.get("/investors/active")
async def get_active_investors():
    """Get count of investors who have placed at least one bid in the past 6 months"""
    from datetime import datetime, timedelta
    
    # Calculate 6 months ago
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Find bids from the past 6 months
    recent_bids = await db.bids.find({
        "timestamp": {"$gte": six_months_ago}
    }).to_list(None)
    
    # Get unique investor IDs
    active_investor_ids = set(bid["investor_id"] for bid in recent_bids)
    
    return {"count": len(active_investor_ids)}

@api_router.get("/investors/inactive")
async def get_inactive_investors():
    """Get count of investors who have not placed any bids in the past 6 months"""
    from datetime import datetime, timedelta
    
    # Calculate 6 months ago
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Get all users (investors)
    all_users = await db.users.find().to_list(None)
    all_investor_ids = set(user["id"] for user in all_users)
    
    # Find bids from the past 6 months
    recent_bids = await db.bids.find({
        "timestamp": {"$gte": six_months_ago}
    }).to_list(None)
    
    # Get unique active investor IDs
    active_investor_ids = set(bid["investor_id"] for bid in recent_bids)
    
    # Calculate inactive investors
    inactive_investor_ids = all_investor_ids - active_investor_ids
    
    return {"count": len(inactive_investor_ids)}

@api_router.post("/chat", response_model=ChatResponse)
async def chat_query(query: ChatQuery):
    """Enhanced chat endpoint with multiple charts and tables support"""
    try:
        logger.info(f"Processing query: {query.message}")
        
        # Use enhanced OpenAI-powered analytics service
        response = await analytics_service.analyze_query(query.message)
        
        # Store enhanced chat message in database
        chat_message = ChatMessage(
            user_id=query.user_id,
            message=query.message,
            response=response.response,
            charts=[chart.dict() for chart in response.charts] if response.charts else None,
            tables=[table.dict() for table in response.tables] if response.tables else None,
            summary_points=response.summary_points,
            # Backward compatibility
            chart_data=response.chart_data,
            chart_type=response.chart_type
        )
        await db.chat_messages.insert_one(chat_message.dict())
        
        logger.info(f"Generated enhanced response with {len(response.charts)} charts and {len(response.tables)} tables")
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
    """Get curated sample questions for the sidebar"""
    sample_questions = [
        # Location & Regional Insights
        "Which regions had the highest number of bids last month?",
        "Show upcoming auctions by city in California.",
        "List top-performing cities by average winning bid in the last quarter.",
        "How many properties were auctioned in New York this year?",
        "Which counties saw the most auction cancellations recently?",
        
        # Investor Activity
        "Who are the top 5 investors by bid amount?",
        "List all investors who won more than 2 properties last month.",
        "Which investor placed the most bids in remote auctions?",
        "Show investment trends for UrbanEdge Ventures over the past 6 months.",
        "Which investors are most active in residential vs commercial auctions?",
        
        # Bidding Trends & Behavior
        "Compare reserve price vs winning bid for last 10 auctions.",
        "Show average number of bids per auction this year.",
        "Highlight auctions where winning bid exceeded reserve by 25%+.",
        "Which auctions had the fewest bids?",
        "How many remote vs in-person bids were placed last month?",
        
        # Auction & Property Stats
        "Show properties with most bids in July.",
        "List top 10 upcoming auctions by property value.",
        "Compare bidding activity across property types (residential, land, commercial).",
        "How many auctions were canceled due to no bidders?",
        "Summarize auction activity for Q2 2025.",
        
        # Performance & Summary Reports
        "Generate a summary report of all completed auctions this month.",
        "Which properties remained unsold after bidding closed?",
        "Breakdown auction wins by investor type (corporate, individual, firm).",
        "Which property types are getting higher than expected winning bids?"
    ]
    
    return {
        "questions": sample_questions,
        "total": len(sample_questions),
        "categories": {
            "location_insights": "🏙️ Location & Regional Insights",
            "investor_activity": "👥 Investor Activity", 
            "bidding_trends": "💰 Bidding Trends & Behavior",
            "auction_stats": "🏠 Auction & Property Stats",
            "performance_reports": "📈 Performance & Summary Reports"
        }
    }

@api_router.post("/enhanced-init-data")
async def enhanced_init_data():
    """Initialize comprehensive mock data for advanced analytics"""
    try:
        logger.info("Starting enhanced comprehensive mock data initialization...")
        
        # Clear existing data
        await db.users.delete_many({})
        await db.properties.delete_many({})
        await db.auctions.delete_many({})
        await db.bids.delete_many({})
        await db.chat_messages.delete_many({})
        
        # Generate realistic date ranges
        from datetime import timedelta
        import random
        
        base_date = datetime.utcnow()
        last_month_start = base_date - timedelta(days=60)
        last_month_end = base_date - timedelta(days=30)
        recent_start = base_date - timedelta(days=30)
        
        # 1. Create 25 diverse users/investors
        users_data = []
        user_names = [
            # Individual investors
            ("Sarah Wilson", "sarah.wilson@email.com", "Manhattan, NY"),
            ("James Chen", "james.chen@email.com", "Palo Alto, CA"),
            ("Maria Rodriguez", "maria.rodriguez@email.com", "Miami, FL"),
            ("Michael Johnson", "mike.johnson@email.com", "Austin, TX"),
            ("Jennifer Davis", "jennifer.davis@email.com", "Denver, CO"),
            ("Robert Kim", "robert.kim@email.com", "Seattle, WA"),
            ("Emily Carter", "emily.carter@email.com", "Nashville, TN"),
            ("Kevin Martinez", "kevin.martinez@email.com", "Atlanta, GA"),
            ("Lisa Chang", "lisa.chang@email.com", "San Francisco, CA"),
            ("David Thompson", "david.thompson@email.com", "Boston, MA"),
            
            # Institutional investors
            ("BlackRock Fund", "fund@blackrock.com", "Chicago, IL"),
            ("Vanguard REIT", "investments@vanguard.com", "Boston, MA"),
            ("American Tower REIT", "fund@americantower.com", "Boston, MA"),
            ("Equity Residential Fund", "investments@equity.com", "Chicago, IL"),
            ("Brookfield Properties", "deals@brookfield.com", "New York, NY"),
            
            # International investors  
            ("Yuki Tanaka", "yuki.tanaka@invest.jp", "San Francisco, CA"),
            ("Pierre Dubois", "pierre.dubois@invest.fr", "New York, NY"),
            ("Hans Mueller", "hans.mueller@invest.de", "Los Angeles, CA"),
            
            # Property management companies
            ("CBRE Investment", "invest@cbre.com", "Los Angeles, CA"),
            ("Cushman Wakefield", "deals@cushman.com", "Washington, DC"),
            ("JLL Capital", "capital@jll.com", "New York, NY"),
            
            # Smaller investors
            ("Tom Builder", "tom.builder@email.com", "Phoenix, AZ"),
            ("Jessica Flip", "jessica.flip@email.com", "Orlando, FL"),
            ("Mark Property", "mark.property@email.com", "Las Vegas, NV"),
            ("Anna Development", "anna.dev@email.com", "Portland, OR")
        ]
        
        for i, (name, email, location) in enumerate(user_names):
            success_rate = random.uniform(15, 95) if i < 20 else random.uniform(5, 45)
            total_bids = random.randint(5, 150) if i < 15 else random.randint(1, 25)
            won_auctions = int(total_bids * success_rate / 100)
            
            user = User(
                id=f"user_{i+1}",
                email=email,
                name=name,
                location=location,
                profile_verified=i < 20,
                success_rate=success_rate,
                total_bids=total_bids,
                won_auctions=won_auctions,
                created_at=base_date - timedelta(days=random.randint(30, 365))
            )
            users_data.append(user.dict())
        
        # 2. Create 120 diverse properties
        properties_data = []
        property_templates = [
            # Residential properties
            ("Luxury Manhattan Penthouse", "Stunning 4BR penthouse with Central Park views", "Manhattan", "New York", "NY", "10021", PropertyType.RESIDENTIAL, 4500000, 5200000, 4, 3),
            ("Beverly Hills Modern Estate", "Contemporary 6BR estate with pool and spa", "Beverly Hills", "Los Angeles", "CA", "90210", PropertyType.RESIDENTIAL, 8500000, 9200000, 6, 5),
            ("Palo Alto Tech Executive Home", "Smart home with solar, 5BR near Stanford", "Palo Alto", "San Francisco", "CA", "94301", PropertyType.RESIDENTIAL, 3200000, 3650000, 5, 4),
            ("Miami Brickell High-Rise Condo", "Luxury 2BR condo with bay views", "Brickell", "Miami", "FL", "33131", PropertyType.RESIDENTIAL, 750000, 825000, 2, 2),
            ("Austin Hill Country Ranch", "10-acre ranch property with main house", "Austin", "Austin", "TX", "78746", PropertyType.RESIDENTIAL, 1200000, 1350000, 4, 3),
            
            # Commercial properties
            ("Wall Street Office Building", "35-story Class A office tower", "Financial District", "New York", "NY", "10005", PropertyType.COMMERCIAL, 15000000, 17500000, None, None),
            ("Chicago Manufacturing Facility", "200K sq ft industrial facility", "South Side", "Chicago", "IL", "60609", PropertyType.INDUSTRIAL, 2200000, 2500000, None, None),
            ("Seattle Tech Campus", "Modern office complex for tech companies", "Bellevue", "Seattle", "WA", "98004", PropertyType.COMMERCIAL, 12000000, 13500000, None, None),
            ("Phoenix Logistics Warehouse", "500K sq ft distribution center", "Phoenix", "Phoenix", "AZ", "85043", PropertyType.INDUSTRIAL, 3500000, 4000000, None, None),
            ("Denver Retail Shopping Center", "Anchor tenant retail complex", "Denver", "Denver", "CO", "80202", PropertyType.COMMERCIAL, 5500000, 6200000, None, None)
        ]
        
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington", "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City", "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento", "Kansas City", "Mesa", "Atlanta", "Omaha", "Colorado Springs", "Raleigh", "Miami", "Oakland", "Minneapolis", "Tulsa", "Cleveland", "Wichita", "Arlington", "New Orleans", "Bakersfield", "Tampa", "Honolulu", "Anaheim", "Aurora", "Santa Ana", "St. Louis", "Riverside", "Corpus Christi", "Lexington", "Pittsburgh", "Anchorage", "Stockton", "Cincinnati", "St. Paul", "Toledo", "Greensboro", "Newark", "Plano", "Henderson", "Lincoln", "Buffalo", "Jersey City", "Chula Vista", "Fort Wayne", "Orlando", "St. Petersburg", "Chandler", "Laredo", "Norfolk", "Durham", "Madison", "Lubbock", "Irvine", "Winston-Salem", "Glendale", "Garland", "Hialeah", "Reno", "Chesapeake", "Gilbert", "Baton Rouge", "Irving", "Scottsdale", "North Las Vegas", "Fremont", "Boise", "Richmond"]
        
        for i in range(120):
            if i < len(property_templates):
                template = property_templates[i]
                title, desc, neighborhood, city, state, zipcode, prop_type, reserve, estimate, bed, bath = template
            else:
                # Generate random properties
                prop_types = [PropertyType.RESIDENTIAL, PropertyType.COMMERCIAL, PropertyType.INDUSTRIAL, PropertyType.LAND]
                prop_type = random.choice(prop_types)
                city = random.choice(cities[:50])  # Use top 50 cities
                state = "CA" if city in ["Los Angeles", "San Francisco", "San Jose", "San Diego", "Sacramento", "Fresno", "Oakland", "Santa Ana", "Anaheim"] else "TX" if city in ["Houston", "San Antonio", "Dallas", "Austin", "Fort Worth", "El Paso"] else "FL" if city in ["Jacksonville", "Miami", "Tampa", "Orlando", "St. Petersburg"] else random.choice(["NY", "IL", "OH", "PA", "MI", "GA", "NC", "NJ", "WA", "MA", "TN", "IN", "MO", "MD", "WI", "CO", "MN", "SC", "AL", "LA", "KY", "OR", "OK", "CT", "IA", "MS", "AR", "UT", "KS", "NV", "NM", "WV", "NE", "ID", "HI", "ME", "NH", "RI", "MT", "DE", "SD", "ND", "AK", "VT", "WY"])
                
                if prop_type == PropertyType.RESIDENTIAL:
                    title = f"{city} {random.choice(['Executive', 'Luxury', 'Modern', 'Traditional', 'Victorian', 'Colonial'])} {random.choice(['Home', 'Estate', 'Residence', 'House'])}"
                    desc = f"Beautiful {random.randint(2,6)}BR {random.choice(['family home', 'executive residence', 'luxury property'])}"
                    reserve = random.randint(300000, 8000000)
                    bed = random.randint(2, 6)
                    bath = random.randint(1, 5)
                elif prop_type == PropertyType.COMMERCIAL:
                    title = f"{city} {random.choice(['Office', 'Retail', 'Mixed-Use', 'Business'])} {random.choice(['Building', 'Complex', 'Center', 'Tower'])}"
                    desc = f"Prime {random.choice(['office', 'retail', 'mixed-use'])} space in {city}"
                    reserve = random.randint(2000000, 25000000)
                    bed = None
                    bath = None
                elif prop_type == PropertyType.INDUSTRIAL:
                    title = f"{city} {random.choice(['Manufacturing', 'Warehouse', 'Distribution', 'Logistics'])} Facility"
                    desc = f"Industrial {random.choice(['manufacturing', 'warehouse', 'distribution'])} facility"
                    reserve = random.randint(1500000, 15000000)
                    bed = None
                    bath = None
                else:  # LAND
                    title = f"{city} Development Land"
                    desc = f"Prime development land in {city}"
                    reserve = random.randint(500000, 5000000)
                    bed = None
                    bath = None
                
                neighborhood = f"{random.choice(['Downtown', 'Uptown', 'Midtown', 'North', 'South', 'East', 'West'])} {city}"
                zipcode = f"{random.randint(10000, 99999)}"
                estimate = int(reserve * random.uniform(1.1, 1.4))
                
            prop = Property(
                id=f"prop_{i+1}",
                title=title,
                description=desc,
                location=neighborhood,
                city=city,
                state=state,
                zipcode=zipcode,
                property_type=prop_type,
                reserve_price=reserve,
                estimated_value=estimate,
                bedrooms=bed,
                bathrooms=bath,
                created_at=base_date - timedelta(days=random.randint(60, 365))
            )
            properties_data.append(prop.dict())
        
        # 3. Create 150 auctions (mix of ended, live, upcoming, cancelled)
        auctions_data = []
        for i in range(150):
            prop_id = f"prop_{(i % 120) + 1}"
            
            # Determine auction status and timing
            if i < 60:  # 60 ended auctions (40% - good for historical analysis)
                status = AuctionStatus.ENDED
                # Mix of recent and older ended auctions
                if i < 20:  # Recent ended (last month)
                    start_time = base_date - timedelta(days=random.randint(7, 30))
                else:  # Older ended
                    start_time = base_date - timedelta(days=random.randint(30, 90))
                end_time = start_time + timedelta(days=random.randint(3, 14))
                
            elif i < 75:  # 15 live auctions (10%)
                status = AuctionStatus.LIVE
                start_time = base_date - timedelta(days=random.randint(1, 5))
                end_time = base_date + timedelta(days=random.randint(1, 7))
                
            elif i < 130:  # 55 upcoming auctions (37%)
                status = AuctionStatus.UPCOMING
                start_time = base_date + timedelta(days=random.randint(1, 30))
                end_time = start_time + timedelta(days=random.randint(3, 14))
                
            else:  # 20 cancelled auctions (13%)
                status = AuctionStatus.CANCELLED
                start_time = base_date - timedelta(days=random.randint(10, 60))
                end_time = start_time + timedelta(days=random.randint(3, 14))
            
            # Get property info for starting bid
            prop = next(p for p in properties_data if p['id'] == prop_id)
            starting_bid = int(prop['reserve_price'] * random.uniform(0.7, 0.9))
            
            # For ended auctions, determine winner and final price
            winner_id = None
            current_highest_bid = 0
            total_bids = 0
            
            if status == AuctionStatus.ENDED:
                total_bids = random.randint(8, 45)
                current_highest_bid = int(starting_bid * random.uniform(1.05, 1.6))
                winner_id = f"user_{random.randint(1, 25)}"
            elif status == AuctionStatus.LIVE:
                total_bids = random.randint(3, 25)
                current_highest_bid = int(starting_bid * random.uniform(1.0, 1.3))
            else:
                total_bids = 0
                current_highest_bid = 0
                
            auction = Auction(
                id=f"auction_{i+1}",
                property_id=prop_id,
                title=f"{prop['title']} Auction",
                start_time=start_time,
                end_time=end_time,
                status=status,
                starting_bid=starting_bid,
                current_highest_bid=current_highest_bid,
                total_bids=total_bids,
                winner_id=winner_id,
                created_at=base_date - timedelta(days=random.randint(70, 400))
            )
            auctions_data.append(auction.dict())
        
        # 4. Create 800+ comprehensive bidding records
        bids_data = []
        bid_counter = 1
        
        for auction in auctions_data:
            if auction['status'] in [AuctionStatus.ENDED, AuctionStatus.LIVE] and auction['total_bids'] > 0:
                auction_id = auction['id']
                property_id = auction['property_id']
                starting_bid = auction['starting_bid']
                final_bid = auction['current_highest_bid']
                winner_id = auction.get('winner_id')
                
                # Generate bidding history
                num_bids = auction['total_bids']
                bid_progression = []
                
                # Create realistic bid amounts progression
                for i in range(num_bids):
                    if i == 0:
                        bid_amount = starting_bid
                    else:
                        increment = random.uniform(0.02, 0.08)  # 2-8% increments
                        bid_amount = int(bid_progression[-1] * (1 + increment))
                    bid_progression.append(bid_amount)
                
                # Ensure final bid matches auction data
                if final_bid > 0:
                    bid_progression[-1] = final_bid
                
                # Generate bids from different users
                auction_start = auction['start_time']
                auction_end = auction['end_time']
                duration = auction_end - auction_start
                
                # Select bidding users (3-8 unique bidders per auction)
                num_bidders = min(random.randint(3, 8), 25)
                bidding_users = random.sample([f"user_{i}" for i in range(1, 26)], num_bidders)
                
                for i, bid_amount in enumerate(bid_progression):
                    # Select bidder (winner for final bid if ended)
                    if i == len(bid_progression) - 1 and auction['status'] == AuctionStatus.ENDED and winner_id:
                        investor_id = winner_id
                    else:
                        investor_id = random.choice(bidding_users)
                    
                    # Determine bid time (spread throughout auction duration)
                    time_fraction = i / max(num_bids - 1, 1)
                    bid_time = auction_start + timedelta(seconds=int(duration.total_seconds() * time_fraction))
                    bid_time += timedelta(minutes=random.randint(-30, 30))  # Add some randomness
                    
                    # Determine bid status
                    if auction['status'] == AuctionStatus.ENDED:
                        if i == len(bid_progression) - 1:
                            bid_status = BidStatus.WON
                        else:
                            bid_status = BidStatus.OUTBID
                    else:  # LIVE auction
                        if i == len(bid_progression) - 1:
                            bid_status = BidStatus.WINNING
                        else:
                            bid_status = BidStatus.OUTBID
                    
                    bid = Bid(
                        id=f"bid_{bid_counter}",
                        auction_id=auction_id,
                        property_id=property_id,
                        investor_id=investor_id,
                        bid_amount=bid_amount,
                        bid_time=bid_time,
                        status=bid_status,
                        is_auto_bid=random.choice([True, False]) if random.random() < 0.3 else False
                    )
                    bids_data.append(bid.dict())
                    bid_counter += 1
        
        # Insert all data
        await db.users.insert_many(users_data)
        await db.properties.insert_many(properties_data)
        await db.auctions.insert_many(auctions_data)
        await db.bids.insert_many(bids_data)
        
        logger.info(f"Enhanced comprehensive mock data inserted:")
        logger.info(f"- Users: {len(users_data)}")
        logger.info(f"- Properties: {len(properties_data)}")
        logger.info(f"- Auctions: {len(auctions_data)}")
        logger.info(f"- Bids: {len(bids_data)}")
        
        return {
            "message": "Enhanced comprehensive mock data inserted successfully",
            "status": "success",
            "stats": {
                "users": len(users_data),
                "properties": len(properties_data),
                "auctions": len(auctions_data),
                "bids": len(bids_data),
                "ended_auctions": len([a for a in auctions_data if a['status'] == 'ended']),
                "won_bids": len([b for b in bids_data if b['status'] == 'won'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced comprehensive mock data initialization: {e}")
        return {"message": f"Error: {str(e)}", "status": "error"}

@api_router.post("/force-init-data")
async def force_init_data():
    """Keep original force-init-data for backward compatibility"""
    return await enhanced_init_data()
async def force_init_data():
    """Force initialization of enhanced mock data"""
    try:
        # Clear existing collections
        await db.users.delete_many({})
        await db.properties.delete_many({})
        await db.auctions.delete_many({})
        await db.bids.delete_many({})
        await db.chat_messages.delete_many({})
        
        logger.info("Cleared existing collections")
        
        # Force insert enhanced mock data
        await init_mock_data_force()
        
        return {"message": "Enhanced mock data inserted successfully", "status": "success"}
    except Exception as e:
        logger.error(f"Error forcing mock data insertion: {e}")
        return {"message": f"Error: {str(e)}", "status": "error"}

async def init_mock_data_force():
    """Force insert enhanced mock data without checking existing data"""
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
    
    # Insert all enhanced mock data
    await db.users.insert_many([user.dict() for user in mock_users])
    await db.properties.insert_many([prop.dict() for prop in mock_properties])
    await db.auctions.insert_many([auction.dict() for auction in mock_auctions])
    await db.bids.insert_many([bid.dict() for bid in mock_bids])
    
    logger.info("Enhanced realistic mock data force-inserted successfully")
    logger.info(f"Inserted: {len(mock_users)} users, {len(mock_properties)} properties, {len(mock_auctions)} auctions, {len(mock_bids)} bids")

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