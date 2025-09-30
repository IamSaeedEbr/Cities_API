# Cities API Project

A FastAPI application for managing city data with caching and logging capabilities.

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI application and route handlers
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── crud.py              # Database operations
│   ├── database.py          # Database configuration
│   ├── cache.py             # Redis caching functions
│   ├── kafka_logger.py      # Kafka logging utility
│   └── populate_cities.py   # Script to populate database from CSV
├── Cities/
│   └── CountryCode-City.csv # Source data file
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Features

- **FastAPI REST API** for city CRUD operations
- **PostgreSQL** database for persistent storage
- **Redis** LRU caching for improved performance
- **Apache Kafka** logging for request monitoring
- **Docker** containerization support

## Getting Started

1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. Populate the database with city data:
   ```bash
   # Run the population script inside the FastAPI container
   docker exec fastapi_app python populate_cities.py
   ```

3. The API is now ready at `http://localhost:8000`

## API Endpoints

- `GET /health` - Health check
- `POST /city` - Create or update a city
- `GET /city/{city_name}` - Retrieve city information

### Insert a new city

```bash
curl -X POST "http://127.0.0.1:8000/city" \
     -H "Content-Type: application/json" \
     -d '{"city": "Berlin", "country_code":"DE"}'
```

### Update an existing city

```bash
curl -X POST "http://127.0.0.1:8000/city" \
     -H "Content-Type: application/json" \
     -d '{"city": "Berlin", "country_code":"GER"}'
```

### Retrieve a city

```bash
curl http://127.0.0.1:8000/city/Berlin
```

If the city exists, you'll get JSON:

```json
{"city": "Berlin", "country_code": "GER", "id": 1}
```

If it doesn't:

```json
{"detail": "City not found"}
```

## Architecture

1. **Database Layer**: PostgreSQL with SQLAlchemy ORM
2. **Caching Layer**: Redis for 10-minute TTL cache
3. **Logging**: Kafka producer for request metrics (latency, cache hit/miss ratio)
4. **API Layer**: FastAPI with Pydantic schemas

## Key Components

- `main.py` - FastAPI application and route handlers
- `models.py` - SQLAlchemy database models
- `schemas.py` - Pydantic request/response schemas
- `crud.py` - Database operations
- `database.py` - Database configuration
- `cache.py` - Redis caching functions
- `kafka_logger.py` - Kafka logging utility
- `populate_cities.py` - Script to populate database from CSV

## Caching Strategy

- Cache hit: Return data from Redis
- Cache miss: Query PostgreSQL, store in Redis, return data
- TTL: 10 minutes per cached item
- LRU eviction policy

## Logging

All requests are logged to Kafka with:
- City name
- Cache hit/miss status
- Response latency (ms)
- Running cache hit ratio


## Verification & Testing

### Check Redis Cache

Connect to Redis and verify cached cities:

```bash
# Connect to Redis container
docker exec -it <redis-container> redis-cli

# List all cached keys
KEYS *

# Get cached data for a specific city
GET "Berlin"

# Check TTL for a key
TTL "Berlin"
```

### Monitor Kafka Logs

View request logs in Kafka:

```bash
# Connect to Kafka container
docker exec -it <kafka-container> /bin/bash

# Create consumer to read logs
kafka-console-consumer --bootstrap-server localhost:9092 --topic request_logs --from-beginning
```

You should see logs like:
```json
{"city": "Berlin", "cache": "miss", "latency_ms": 45.2, "hit_ratio": 0.25}
{"city": "Berlin", "cache": "hit", "latency_ms": 2.1, "hit_ratio": 0.33}
```

### Test Cache Behavior

1. Make the same request twice:
   ```bash
   curl http://127.0.0.1:8000/city/Berlin  # First request (cache miss)
   curl http://127.0.0.1:8000/city/Berlin  # Second request (cache hit)
   ```

2. Check Kafka logs to verify hit/miss status and latency differences
3. Verify in Redis that the city is cached with proper TTL (600 seconds)
