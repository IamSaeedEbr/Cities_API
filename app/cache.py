import os
import redis
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MAX_CACHE_SIZE = 10  # Maximum number of cached items

# Main cache - database 0 (default)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# Tracker - separate database 1 (hidden from main cache view)
tracker_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)

CACHE_KEY_PREFIX = "city:"
CACHE_TRACKER = "cache_tracker"

def get_from_cache(key: str):
    try:
        cache_key = f"{CACHE_KEY_PREFIX}{key}"
        value = redis_client.get(cache_key)
        
        if value:
            # Update access time for LRU tracking
            tracker_client.zadd(CACHE_TRACKER, {key: tracker_client.time()[0]})
            return json.loads(value)
        return None
    except (redis.RedisError, json.JSONDecodeError):
        # Return None if Redis is unavailable or JSON parsing fails
        return None

def set_to_cache(key: str, value: dict, ttl: int = 600):
    try:
        cache_key = f"{CACHE_KEY_PREFIX}{key}"
        
        # Check current cache size
        current_size = tracker_client.zcard(CACHE_TRACKER)
        
        # If cache is full and this is a new key, remove oldest
        if current_size >= MAX_CACHE_SIZE and not redis_client.exists(cache_key):
            # Get the oldest key (lowest score in sorted set)
            oldest_keys = tracker_client.zrange(CACHE_TRACKER, 0, 0)
            if oldest_keys:
                oldest_key = oldest_keys[0]
                # Remove from cache and tracker
                redis_client.delete(f"{CACHE_KEY_PREFIX}{oldest_key}")
                tracker_client.zrem(CACHE_TRACKER, oldest_key)
        
        # Add new item to cache
        redis_client.set(cache_key, json.dumps(value), ex=ttl)
        
        # Track this key with current timestamp
        tracker_client.zadd(CACHE_TRACKER, {key: tracker_client.time()[0]})
        
    except (redis.RedisError, json.JSONEncodeError):
        # Silently fail if caching is unavailable - application should continue working
        pass
