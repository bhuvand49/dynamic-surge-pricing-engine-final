import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "").strip()

if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is missing")

try:
    redis_client = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
        retry_on_timeout=True,
        ssl_cert_reqs=None
    )

    redis_client.ping()
    print("[OK] Connected to Upstash Redis")

except Exception as e:
    raise RuntimeError(f"Failed to connect to Upstash Redis: {e}")