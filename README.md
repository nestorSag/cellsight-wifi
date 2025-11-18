# WiFi Data Search API

A lightweight FastAPI backend for querying WiFi access point data from QuestDB.

## Features

- **OOP Query Building**: Uses SQLAlchemy ORM for type-safe, method-chaining query construction
- **Time Range Queries**: Required `from` and `to` timestamps to delimit the query window
- **Indexed Filters**: Optional filters on indexed columns for efficient querying:
  - `ap_id`: Access Point ID
  - `channel`: WiFi channel
  - `band`: WiFi band (e.g., "2.4GHz", "5GHz")
  - `state`: Geographic state
  - `region`: Geographic region

## Architecture

The backend is designed to act as a secure intermediary between clients and the QuestDB instance, which is not exposed to the internet.

### Components

- **`src/models.py`**: SQLAlchemy ORM model for the `wifi` table
- **`src/backend.py`**: FastAPI application with the `/search` endpoint
- **`src/test_api.py`**: Test script demonstrating API usage

## Running the Server

### Option 1: Direct Python execution
```bash
python src/backend.py
```

### Option 2: Using uvicorn
```bash
uvicorn src.backend:app --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

### `GET /`
Root endpoint with API information.

### `GET /health`
Health check endpoint.

### `POST /search`
Search WiFi data with time range and optional filters.

**Request Body:**
```json
{
  "from": "2025-11-17T00:00:00",
  "to": "2025-11-18T00:00:00",
  "ap_id": "optional-ap-id",
  "channel": "optional-channel",
  "band": "optional-band",
  "state": "optional-state",
  "region": "optional-region"
}
```

**Response:**
```json
{
  "count": 100,
  "data": [
    {
      "timestamp": "2025-11-17T12:30:00",
      "ap_id": "ap-001",
      "avg_rssi": -65.5,
      "channel": "6",
      "band": "2.4GHz",
      "state": "CA",
      "region": "West",
      ...
    }
  ]
}
```

## Example Usage

### Using curl
```bash
# Basic search with time range only
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "2025-11-17T00:00:00",
    "to": "2025-11-18T00:00:00"
  }'

# Search with filters
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "2025-11-17T00:00:00",
    "to": "2025-11-18T00:00:00",
    "band": "5GHz",
    "state": "CA"
  }'
```

### Using Python
```python
import requests
from datetime import datetime, timedelta

# Define time range
to_ts = datetime.now()
from_ts = to_ts - timedelta(hours=24)

# Basic search
response = requests.post(
    "http://localhost:8000/search",
    json={
        "from": from_ts.isoformat(),
        "to": to_ts.isoformat()
    }
)
data = response.json()
print(f"Found {data['count']} results")

# Search with filters
response = requests.post(
    "http://localhost:8000/search",
    json={
        "from": from_ts.isoformat(),
        "to": to_ts.isoformat(),
        "band": "5GHz",
        "state": "CA"
    }
)
data = response.json()
print(f"Found {data['count']} filtered results")
```

### Using the test script
```bash
python src/test_api.py
```

## SQLAlchemy Query Building

The backend uses SQLAlchemy's ORM for type-safe query construction. Here's how it works:

```python
# Start with base query
query = session.query(WiFi)

# Chain filters using method calls
query = query.filter(
    and_(
        WiFi.timestamp >= from_ts,
        WiFi.timestamp < to_ts
    )
)

# Add indexed filters conditionally
if band:
    query = query.filter(WiFi.band == band)
if state:
    query = query.filter(WiFi.state == state)

# Execute query
results = query.all()
```

This approach provides:
- **Type safety**: Catch errors at development time
- **IDE support**: Auto-completion for columns
- **SQL injection protection**: Automatic parameterization
- **Readable code**: Method chaining is intuitive
- **Flexibility**: Easy to add complex conditions

## Configuration

The backend reads database connection details from `config/main.yaml`:

```yaml
db:
  auth:
    username: admin
    password: quest
    host: localhost
    db: qdb
  params:
    query_port: 8812
    table_name: wifi
    indexes:
      - ap_id
      - channel
      - band
      - state
      - region
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide an interactive interface to test the API directly from your browser.
