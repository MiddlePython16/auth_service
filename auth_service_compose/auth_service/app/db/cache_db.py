from typing import Optional

from services.base_cache import CacheStorage
from utils.exceptions import CantGetInitializedObjectError

cache: Optional[CacheStorage] = None


def get_cache_db() -> CacheStorage:
    if not cache:
        raise CantGetInitializedObjectError(object_name='cache storage')
    return cache
