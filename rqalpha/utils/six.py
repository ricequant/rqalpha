try:
    from functools import lru_cache
except ImportError:
    from fastcache import lru_cache
