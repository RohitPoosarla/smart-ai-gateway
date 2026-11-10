from collections import OrderedDict
from copy import deepcopy
from threading import Lock
from time import monotonic


cache = OrderedDict()
cache_lock = Lock()

CACHE_TTL_SECONDS = 300
MAX_CACHE_ENTRIES = 100


def get_cached_response(key):
    with cache_lock:
        entry = cache.get(key)

        if entry is None:
            return None

        expires_at, data = entry

        if monotonic() >= expires_at:
            del cache[key]
            return None

        cache.move_to_end(key)
        return deepcopy(data)


def save_cached_response(key, data):
    with cache_lock:
        cache[key] = (
            monotonic() + CACHE_TTL_SECONDS,
            deepcopy(data),
        )
        cache.move_to_end(key)

        while len(cache) > MAX_CACHE_ENTRIES:
            cache.popitem(last=False)