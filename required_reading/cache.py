from django.core.cache import caches
from django.core.cache.backends.dummy import DummyCache

CACHE_TIMEOUT_SECONDS = 300
KEY_PREFIX = "required_reading"


def get_cache():
    """Return the project's default Django cache backend, or a dummy cache if unavailable."""
    try:
        return caches["default"]
    except Exception:  # pragma: no cover - defensive fallback for unusual standalone setups
        return DummyCache("required-reading-dummy", {})


def cache_key(name):
    return "{}:{}".format(KEY_PREFIX, name)


def get_cached(key, default=None):
    return get_cache().get(cache_key(key), default)


def set_cached(key, value, timeout=CACHE_TIMEOUT_SECONDS):
    get_cache().set(cache_key(key), value, timeout)


def delete_cached(key):
    get_cache().delete(cache_key(key))


def clear_required_reading_cache():
    cache = get_cache()
    for key in ["settings", "active_document_ids"]:
        cache.delete(cache_key(key))
