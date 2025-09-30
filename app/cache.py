import os
import redis
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# decode_responses=True makes Redis return strings instead of bytes
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_from_cache(key: str):
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except (redis.RedisError, json.JSONDecodeError):
        # Return None if Redis is unavailable or JSON parsing fails
        return None

def set_to_cache(key: str, value: dict, ttl: int = 600):
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
    except (redis.RedisError, json.JSONEncodeError):
        # Silently fail if caching is unavailable - application should continue working
        pass