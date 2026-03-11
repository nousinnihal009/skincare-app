import time
from typing import Optional
from fastapi import HTTPException, Request

_rate_limit_counters: dict[str, list[float]] = {}

try:
    import redis.asyncio as aioredis
    import os
    from dotenv import load_dotenv

    load_dotenv()
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_pool: Optional[aioredis.Redis] = aioredis.from_url(
        REDIS_URL, decode_responses=True
    )
except Exception:
    _redis_pool = None

async def _redis_available() -> bool:
    if _redis_pool is None:
        return False
    try:
        await _redis_pool.ping()
        return True
    except Exception:
        return False

def create_rate_limiter(limit: int, window_seconds: int = 60):
    async def rate_limit_dependency(req: Request) -> None:
        user_id = getattr(req.state, 'user_id', None)
        if not user_id:
            user_id = req.client.host if req.client else "unknown"
            
        now = time.time()
        window_start = now - window_seconds

        if await _redis_available():
            assert _redis_pool is not None
            rkey = f"dermai:rate:{user_id}"
            pipe = _redis_pool.pipeline()
            await pipe.zremrangebyscore(rkey, 0, window_start)
            await pipe.zadd(rkey, {str(now): now})
            await pipe.zcard(rkey)
            await pipe.expire(rkey, window_seconds * 2)
            results = await pipe.execute()
            count = results[2]
            if count > limit:
                raise HTTPException(status_code=429, detail="Too Many Requests", headers={"Retry-After": str(window_seconds)})
        else:
            entries = _rate_limit_counters.get(user_id, [])
            entries = [t for t in entries if t > window_start]
            entries.append(now)
            _rate_limit_counters[user_id] = entries
            if len(entries) > limit:
                raise HTTPException(status_code=429, detail="Too Many Requests", headers={"Retry-After": str(window_seconds)})
                
    return rate_limit_dependency
