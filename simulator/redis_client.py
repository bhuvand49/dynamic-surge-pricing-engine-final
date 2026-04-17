import os
import time
import redis

# ---------------------------------
# CLOUD REDIS URL (Upstash / Render / Local)
# ---------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")

# ---------------------------------
# Try Redis Connection
# ---------------------------------
try:
    redis_client = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True
    )
    redis_client.ping()
    print("[OK] Connected to Redis")
    print(f"[INFO] Redis URL: {REDIS_URL}")

except Exception as e:
    print("[ERROR] Redis connection failed:", e)
    print("[INFO] Using in-memory fallback")

    # ---------------------------------
    # In-Memory Fallback
    # ---------------------------------
    class InMemoryRedis:
        def __init__(self):
            self.data = {}
            self.expiry = {}

        def _cleanup(self):
            now = time.time()
            expired = [
                key for key, exp in self.expiry.items()
                if now > exp
            ]
            for key in expired:
                self.data.pop(key, None)
                self.expiry.pop(key, None)

        def hset(self, key, mapping=None, **kwargs):
            self._cleanup()
            self.data[key] = dict(mapping or kwargs)
            return 1

        def hgetall(self, key):
            self._cleanup()
            return self.data.get(key, {})

        def expire(self, key, seconds):
            self.expiry[key] = time.time() + seconds
            return 1

        def delete(self, key):
            self.data.pop(key, None)
            self.expiry.pop(key, None)
            return 1

        def keys(self, pattern="*"):
            self._cleanup()
            if pattern == "*":
                return list(self.data.keys())

            prefix = pattern.replace("*", "")
            return [
                k for k in self.data.keys()
                if k.startswith(prefix)
            ]

        def scan_iter(self, pattern="*"):
            for k in self.keys(pattern):
                yield k

        def ping(self):
            return True

    redis_client = InMemoryRedis()