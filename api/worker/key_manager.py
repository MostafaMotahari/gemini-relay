import time

from redis_client import redis_client


def get_available_key():
    now = int(time.time())

    keys = redis_client.keys("apikey:*")

    available = []

    for key_name in keys:
        data = redis_client.hgetall(key_name)

        if not data:
            continue

        disabled = int(data.get("disabled", 0))
        usage = int(data.get("usage", 0))
        max_usage = int(data.get("max_usage", 0))
        cooldown_until = int(data.get("cooldown_until", 0))

        if disabled:
            continue

        if max_usage > 0 and usage >= max_usage:
            continue

        if cooldown_until > now:
            continue

        available.append((key_name, usage, data))

    if not available:
        return None

    available.sort(key=lambda x: x[1])

    selected = available[0]

    redis_client.hincrby(selected[0], "usage", 1)
    redis_client.hset(selected[0], "last_used", now)

    return {
        "redis_key": selected[0],
        "api_key": selected[2]["key"]
    }


def cooldown_key(redis_key: str, seconds: int):
    redis_client.hset(
        redis_key,
        "cooldown_until",
        int(time.time()) + seconds
    )