import json
from abc import ABC, abstractmethod

from extensions.tracer import trace_decorator
from redis import Redis  # type: ignore
from redis.client import Pipeline  # type: ignore


class CachePipeline(ABC):
    @abstractmethod
    def incr(self, key: str, amount: int, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def expire(self, key: str, expire: int, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def execute(self, **kwargs):
        pass  # noqa: WPS420


class CacheStorage(ABC):
    @abstractmethod
    def get(self, key: str, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def set(self, key: str, cache_value: str, expire: int, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def close(self):
        pass  # noqa: WPS420

    @abstractmethod
    def pipeline(self):
        pass  # noqa: WPS420


class BaseRedisPipeline(CachePipeline):
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    def incr(self, key: str, amount: int, **kwargs):
        self.pipeline.incr(key, amount)

    def expire(self, key: str, expire: int, **kwargs):
        self.pipeline.expire(key, expire)

    def execute(self):
        return self.pipeline.execute()


class BaseRedisStorage(CacheStorage):
    def __init__(self, redis: Redis):
        self.redis = redis

    def get(self, key: str, **kwargs):
        return self.redis.get(name=key)

    def set(self, key: str, cache_value: str, expire: int, **kwargs):
        return self.redis.set(name=key, value=cache_value, ex=expire)

    def close(self):
        self.redis.close()

    def pipeline(self) -> CachePipeline:
        return BaseRedisPipeline(pipeline=self.redis.pipeline())


class BaseCacheStorage:
    def __init__(self, cache: CacheStorage, **kwargs):
        super().__init__(**kwargs)

        self.cache = cache
        self.CACHE_EXPIRE_IN_SECONDS = 10

    @trace_decorator()
    def get_one_item_from_cache(self, cache_key: str, model):
        cache_data = self.cache.get(key=cache_key)

        if not cache_data:
            return None

        return model.parse_raw(cache_data)

    @trace_decorator()
    def put_one_item_to_cache(self, cache_key: str, entity, expire=None):
        self.cache.set(
            key=cache_key,
            cache_value=entity.json(),
            expire=self.CACHE_EXPIRE_IN_SECONDS if expire is None else expire,
        )

    @trace_decorator()
    def get_items_from_cache(self, cache_key: str, model):
        cache_data = self.cache.get(key=cache_key)
        if not cache_data:
            return []

        return [model.parse_raw(entity) for entity in json.loads(cache_data)]

    @trace_decorator()
    def put_items_to_cache(self, cache_key: str, entities: list, expire=None):
        self.cache.set(
            key=cache_key,
            cache_value=json.dumps([entity.json() for entity in entities]),
            expire=self.CACHE_EXPIRE_IN_SECONDS if expire is None else expire,
        )
