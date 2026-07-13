import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Redis
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

def set_cache(key: str, value: dict, ttl: int = 60):
    """Save data to cache with expiry time in seconds"""
    try:
        r.setex(key, ttl, json.dumps(value))
        return True
    except:
        return False

def get_cache(key: str):
    """Get data from cache"""
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
        return None
    except:
        return None

def delete_cache(key: str):
    """Delete a cache entry"""
    try:
        r.delete(key)
    except:
        pass

def clear_product_cache():
    """Clear all product related cache"""
    try:
        keys = r.keys("product:*")
        if keys:
            r.delete(*keys)
    except:
        pass