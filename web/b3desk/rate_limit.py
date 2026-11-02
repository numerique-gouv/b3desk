import time
from functools import wraps

from flask import abort
from flask import current_app
from flask import g
from flask import request
from flask_caching.backends import RedisCache
from redis.exceptions import RedisError

from b3desk import cache


def visio_code_counter(kind, increment=False, reset=False):
    """Count per IP and user in shared, expiring Redis windows."""
    window = current_app.config["VISIO_CODE_RATE_WINDOW"]
    identities = [f"ip:{request.remote_addr or 'unknown'}"]
    if user := getattr(g, "user", None):
        identities.append(f"user:{user.id}")
    bucket = int(time.time()) // window
    counts = []
    if not current_app.testing and not isinstance(cache.cache, RedisCache):
        abort(503)
    try:
        for identity in identities:
            key = f"visio-code:{kind}:{bucket}:{identity}"
            if reset:
                cache.delete(key)
            if increment:
                # Retain the key past the window boundary so concurrent INCRs
                # cannot race its expiry. Redis ADD and INCR are atomic.
                cache.add(key, 0, timeout=2 * window)
                counts.append(cache.cache.inc(key))
            else:
                counts.append(cache.get(key) or 0)
    except RedisError, OSError:
        current_app.logger.warning("Visio code counter unavailable")
        abort(503)
    return max(counts)


def visio_code_rate_limit(view):
    @wraps(view)
    def limited(*args, **kwargs):
        if (
            visio_code_counter("requests", increment=True)
            > current_app.config["VISIO_CODE_RATE_LIMIT"]
        ):
            window = current_app.config["VISIO_CODE_RATE_WINDOW"]
            abort(429, retry_after=window - int(time.time()) % window)
        return view(*args, **kwargs)

    return limited
