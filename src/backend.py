import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from src.models import WiFi
from src.utils import load_config

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="WiFi Data Search API",
    description="API for querying WiFi access point data from QuestDB",
    version="1.0.0"
)

# Database connection - will be initialized lazily
engine = None
SessionLocal = None


def get_db_session():
    """Lazy initialization of database connection"""
    global engine, SessionLocal
    
    if engine is None:
        # Load configuration
        cfg = load_config()
        db_config = cfg.db
        
        # Create database connection
        connection_string = (
            f"postgresql://{db_config.auth.username}:{db_config.auth.password}"
            f"@{db_config.auth.host}:{db_config.params.query_port}/{db_config.auth.db}"
        )
        engine = create_engine(connection_string)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return SessionLocal()


class SearchRequest(BaseModel):
    """Request model for the search endpoint"""
    from_ts: datetime = Field(None, description="Start timestamp for the query time window", alias="from")
    to_ts: datetime = Field(None, description="End timestamp for the query time window", alias="to")
    ap_id: Optional[str] = Field(None, description="Filter by access point ID")
    channel: Optional[str] = Field(None, description="Filter by channel")
    band: Optional[str] = Field(None, description="Filter by band")
    state: Optional[str] = Field(None, description="Filter by state")
    region: Optional[str] = Field(None, description="Filter by region")

    class Config:
        populate_by_name = True

    # if None, set from_ts to now - 24 hrs and to_ts to now
    @model_validator(mode="before")
    @classmethod
    def add_default_timestamps(cls, values):
        if values.get("from") is None or values.get("to") is None:
            now = datetime.utcnow()
            if values.get("from") is None:
                values["from"] = (now - timedelta(hours=24)).isoformat()
            if values.get("to") is None:
                values["to"] = now.isoformat()
        return values
        


class SearchResponse(BaseModel):
    """Response model for the search endpoint"""
    count: int
    data: List[Dict[str, Any]]


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "WiFi Data Search API",
        "endpoints": {
            "/search": "POST - Search WiFi data with time range and filters"
        }
    }


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """
    Search WiFi data with time range and optional filters.
    
    The indexed qualifiers (filters) that can be used are:
    - ap_id: Access Point ID
    - channel: WiFi channel
    - band: WiFi band
    - state: Geographic state
    - region: Geographic region
    
    All filters are optional and can be combined in any way.
    """
    try:
        session = get_db_session()
        
        # Start building the query using SQLAlchemy ORM
        query = session.query(WiFi)
        
        # Apply time range filter (required)
        query = query.filter(
            and_(
                WiFi.timestamp >= request.from_ts,
                WiFi.timestamp < request.to_ts
            )
        )
        
        # Apply optional indexed filters
        if request.ap_id is not None:
            query = query.filter(WiFi.ap_id == request.ap_id)
        
        if request.channel is not None:
            query = query.filter(WiFi.channel == request.channel)
        
        if request.band is not None:
            query = query.filter(WiFi.band == request.band)
        
        if request.state is not None:
            query = query.filter(WiFi.state == request.state)
        
        if request.region is not None:
            query = query.filter(WiFi.region == request.region)
        
        # Log the query for debugging
        logger.info(f"Executing query: {query}")
        
        # Execute query
        results = query.all()
        
        # Convert results to dictionaries
        data = []
        for row in results:
            row_dict = {
                column.name: getattr(row, column.name)
                for column in WiFi.__table__.columns
            }
            # Convert datetime to ISO format string
            if row_dict['timestamp']:
                row_dict['timestamp'] = row_dict['timestamp'].isoformat()
            data.append(row_dict)
        
        session.close()
        
        logger.info(f"Query returned {len(data)} results")
        
        return SearchResponse(count=len(data), data=data)
    
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
