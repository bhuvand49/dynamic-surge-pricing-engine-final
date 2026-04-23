import os
import time
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379").strip().strip('"').strip("'")


try:
    redis_client = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    redis_client.ping()
    print("[OK] Connected to Redis")

except Exception as e:
    print("[WARN] Redis failed, using memory store:", e)

    class InMemoryRedis:
        def __init__(self):
            self.data = {}
            self.expiry = {}

        def _cleanup(self):
            now = time.time()
            expired = [k for k, v in self.expiry.items() if now > v]

            for k in expired:
                self.data.pop(k, None)
                self.expiry.pop(k, None)

        def hset(self, key, mapping=None, **kwargs):
            self._cleanup()
            if key not in self.data:
                self.data[key] = {}

            payload = dict(mapping or kwargs)
            self.data[key].update(payload)
            return 1

        def hgetall(self, key):
            self._cleanup()
            return self.data.get(key, {})

        def hget(self, key, field):
            self._cleanup()
            return self.data.get(key, {}).get(field)

        def expire(self, key, seconds):
            self.expiry[key] = time.time() + seconds
            return 1

        def delete(self, key):
            self.data.pop(key, None)
            self.expiry.pop(key, None)
            return 1

        def scan_iter(self, pattern="*"):
            self._cleanup()
            prefix = pattern.replace("*", "")
            for key in list(self.data.keys()):
                if key.startswith(prefix):
                    yield key

        def ping(self):
            return True

    redis_client = InMemoryRedis()