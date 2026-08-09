import os
import json
import hashlib
import structlog
from pathlib import Path
# pyrefly: ignore [missing-import]
from src.config import settings

logger = structlog.get_logger(__name__)

# Setup local cache directory fallback
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Try to initialize redis client
try:
    import redis
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
    USE_REDIS = True
except Exception as e:
    logger.warning("redis_unavailable_falling_back_to_local", error=str(e))
    USE_REDIS = False
    redis_client = None

def _get_cache_key(agent_name: str, input_str: str) -> str:
    hash_object = hashlib.md5(input_str.encode("utf-8"))
    return f"{agent_name}_{hash_object.hexdigest()}"

def _get_file_path(cache_key: str) -> Path:
    safe_key = cache_key.replace("/", "_").replace("\\", "_")
    return CACHE_DIR / f"{safe_key}.json"

def get_cached(agent_name: str, input_str: str) -> dict | None:
    cache_key = _get_cache_key(agent_name, input_str)
    
    if USE_REDIS and redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error("redis_get_error", error=str(e))
    
    # Fallback to local file
    path = _get_file_path(cache_key)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def set_cached(agent_name: str, input_str: str, response_json: dict):
    cache_key = _get_cache_key(agent_name, input_str)
    
    if USE_REDIS and redis_client:
        try:
            # Set TTL to 24 hours (86400 seconds)
            redis_client.setex(cache_key, 86400, json.dumps(response_json))
            return
        except Exception as e:
            logger.error("redis_set_error", error=str(e))
            
    # Fallback to local file
    path = _get_file_path(cache_key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(response_json, f)
    except Exception as e:
        logger.error("file_cache_set_error", error=str(e))
