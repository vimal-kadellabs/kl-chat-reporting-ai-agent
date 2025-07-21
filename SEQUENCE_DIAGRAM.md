# Real Estate Auction Analytics - Sequence Diagram

## Complete Data Flow and Logic Architecture

```mermaid
sequenceDiagram
    participant U as User Browser
    participant FE as React Frontend
    participant API as FastAPI Backend
    participant LLM as OpenAI GPT-4
    participant DB as MongoDB
    participant AS as Analytics Service

    Note over U,DB: 🏠 Real Estate Auction Analytics Platform

    %% Initial Dashboard Load
    rect rgb(240, 248, 255)
        Note over U,DB: Dashboard Initialization
        U->>FE: Access Application
        FE->>API: GET /api/users
        API->>DB: db.users.find()
        DB-->>API: User data
        API-->>FE: JSON response
        
        FE->>API: GET /api/properties
        API->>DB: db.properties.find()
        DB-->>API: Property data
        API-->>FE: JSON response
        
        FE->>API: GET /api/auctions
        API->>DB: db.auctions.find()
        DB-->>API: Auction data
        API-->>FE: JSON response
        
        FE->>API: GET /api/bids
        API->>DB: db.bids.find()
        DB-->>API: Bid data
        API-->>FE: JSON response
        
        FE->>API: GET /api/investors/active
        API->>DB: db.bids.find({timestamp: {$gte: 6_months_ago}})
        DB-->>API: Recent bids data
        API-->>API: Calculate unique active investors
        API-->>FE: {count: active_investors}
        
        FE->>API: GET /api/investors/inactive
        API->>DB: db.users.find() & db.bids.find()
        DB-->>API: All users & recent bids
        API-->>API: Calculate inactive investors
        API-->>FE: {count: inactive_investors}
        
        FE-->>U: Dashboard with metrics cards displayed
    end

    %% Chat Interface Interaction
    rect rgb(248, 250, 252)
        Note over U,DB: Natural Language Query Processing
        U->>FE: Click "Start Chat"
        FE-->>U: Chat Interface loaded
        
        U->>FE: Type query: "Which regions had highest bids last month?"
        FE->>API: POST /api/chat {message: "Which regions..."}
        
        API->>AS: analytics_service.analyze_query(message)
        AS->>AS: _is_query_domain_relevant(message)
        Note right of AS: Domain validation check
        
        AS->>AS: _detect_intent(message)
        Note right of AS: Intent: "regional_analysis"
        
        %% Data Fetching Phase
        AS->>DB: db.users.find()
        DB-->>AS: Users data
        AS->>DB: db.properties.find()
        DB-->>AS: Properties data
        AS->>DB: db.auctions.find()
        DB-->>AS: Auctions data
        AS->>DB: db.bids.find()
        DB-->>AS: Bids data
        
        %% LLM Processing Phase
        AS->>LLM: POST /v1/chat/completions
        Note right of LLM: System Prompt + User Query + Data Context
        Note right of LLM: Function calling for structured response
        
        LLM-->>AS: Structured JSON Response
        Note left of AS: {response: "markdown", charts: [...], tables: [...], summary_points: [...]}
        
        AS->>AS: Parse and validate response
        AS->>AS: Handle chart data formatting
        AS->>AS: Process table structures
        
        AS-->>API: Enhanced ChatResponse object
        API-->>FE: JSON {response, charts, tables, summary_points}
        
        %% Frontend Rendering
        FE->>FE: Process multiple charts data
        FE->>FE: Process tables data
        FE->>FE: Render charts in 2-column grid
        FE->>FE: Render full-width tables
        FE->>FE: Apply typing animation to text
        
        FE-->>U: Interactive response with charts & tables
    end

    %% Sample Questions Load
    rect rgb(245, 255, 245)
        Note over U,DB: Sample Questions Feature
        FE->>API: GET /api/sample-questions
        API->>API: Return predefined questions
        API-->>FE: Sample questions array
        FE-->>U: Sidebar with clickable questions
        
        U->>FE: Click sample question
        Note over U,FE: Triggers same chat flow as above
    end

    %% Error Handling & Fallbacks
    rect rgb(255, 245, 245)
        Note over U,DB: Error Handling
        alt Domain Irrelevant Query
            AS->>AS: _is_query_domain_relevant() returns False
            AS-->>API: Domain-specific error message
            API-->>FE: Error response
            FE-->>U: "Please ask real estate related questions"
        else LLM Processing Fails
            AS->>AS: create_manual_response() fallback
            AS-->>API: Manual response with basic charts
            API-->>FE: Fallback response
            FE-->>U: Basic response with available data
        else Database Error
            API-->>FE: Error response
            FE-->>U: "Unable to fetch data" message
        end
    end
```

## Key Components Breakdown

### 🎯 **Analytics Service (AS) - Core Logic Engine**
- **Intent Detection**: Analyzes user queries to determine analysis type
- **Domain Validation**: Ensures queries are real estate auction related
- **Data Aggregation**: Combines data from multiple DB collections
- **LLM Orchestration**: Manages OpenAI API calls with context

### 🤖 **OpenAI LLM Integration**
- **Model**: GPT-4 with function calling capability
- **Input**: System prompt + user query + aggregated data context
- **Output**: Structured JSON with multiple charts, tables, and insights
- **Function Calling**: Used for structured response formatting

### 🗄️ **MongoDB Collections**
- **users**: Investor/user profiles
- **properties**: Real estate property data
- **auctions**: Auction events with status tracking
- **bids**: Bid history with timestamps and amounts

### 🔄 **Data Processing Pipeline**
1. **Query Reception**: User input received via React frontend
2. **Intent Analysis**: Backend determines query type and relevance
3. **Data Aggregation**: Multiple DB collections queried in parallel
4. **LLM Enhancement**: OpenAI processes data with natural language context
5. **Response Structuring**: Multiple charts and tables generated
6. **Frontend Rendering**: React components display interactive visualizations

### 📊 **Chart & Table Rendering**
- **Charts**: Recharts library with ResponsiveContainer (320px height)
- **Layout**: 2-column grid for charts, full-width for tables
- **Interactivity**: Sorting, pagination, CSV download for tables
- **Loading States**: Progress bars and skeleton placeholders

### 🔧 **API Endpoints Overview**
- `GET /api/users` - All registered investors
- `GET /api/properties` - Available auction properties  
- `GET /api/auctions` - Auction events and status
- `GET /api/bids` - Bidding history and amounts
- `GET /api/investors/active` - Active investors (6 months)
- `GET /api/investors/inactive` - Inactive investors
- `GET /api/sample-questions` - Predefined query examples
- `POST /api/chat` - Main analytics query endpoint

### ⚡ **Performance Optimizations**
- **Parallel API Calls**: Dashboard metrics fetched simultaneously
- **Database Indexing**: Efficient queries on timestamp and status fields
- **Response Caching**: LLM responses structured for quick rendering
- **Lazy Loading**: Components render progressively

### 🛡️ **Error Handling Strategy**
- **Domain Validation**: Filters non-real estate queries
- **Fallback Responses**: Manual charts when LLM fails
- **Graceful Degradation**: Basic functionality maintained during errors
- **User Feedback**: Clear error messages and loading states