from functools import lru_cache

from db.cache_db import get_cache_db
from db.db import get_db
from extensions.tracer import trace_decorator
from models.models import Oauth, OAuthEnum
from services.base_cache import BaseCacheStorage
from services.base_main import BaseMainStorage


class OauthService(BaseCacheStorage, BaseMainStorage):
    cache_model = None

    @trace_decorator()
    def get_oauth(self, sub: str, oauth_type: OAuthEnum) -> Oauth:
        return self.filter_by(sub=sub, type=oauth_type, _first=True)

    @trace_decorator()
    def create_oauth(self, oauth_params: dict):
        self.create(**oauth_params)


@lru_cache()
def get_oauth_service() -> OauthService:
    return OauthService(
        cache=get_cache_db(),
        db=get_db(),
        db_model=Oauth,
    )
