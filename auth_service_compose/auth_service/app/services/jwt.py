from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

from db.cache_db import get_cache_db
from db.db import get_db
from extensions.tracer import trace_decorator
from flask import Response, current_app
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                set_access_cookies, set_refresh_cookies)
from models import models
from pydantic import BaseModel
from services.base_cache import BaseCacheStorage
from services.base_main import BaseMainStorage
from services.refresh_token import get_refresh_token_service


class Token(BaseModel):
    jti: str


class JWTService(BaseCacheStorage, BaseMainStorage):
    cache_model = Token
    db_model = models.RefreshToken

    @trace_decorator()
    def authorize(self, response: Response, user) -> Response:
        refresh_token = self.create_refresh_token(user=user)

        token = self.create_access_token(user=user)

        set_access_cookies(response, token)
        set_refresh_cookies(response, refresh_token)
        return response

    @trace_decorator()
    def create_access_token(
            self,
            user,
            additional_claims: Optional[dict] = None,
    ) -> str:
        return create_access_token(
            identity=user,
            additional_claims=additional_claims,
            fresh=True,
        )

    @trace_decorator()
    def create_refresh_token(self, user) -> str:
        token = create_refresh_token(identity=user)
        refresh_token_service = get_refresh_token_service()

        now = datetime.now(timezone.utc)

        refresh_token_service.create_refresh_token(
            refresh_token_params={'user_id': user.id,
                                  'token': token,
                                  'from_': now,
                                  'to': now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES']},
        )
        return token

    @trace_decorator()
    def block_token(self, cache_key: str, expire: timedelta):
        self.put_one_item_to_cache(
            cache_key=cache_key,
            entity=self.cache_model(jti=cache_key),
            expire=expire,
        )

    @trace_decorator()
    def get_blocked_token(self, cache_key: str):
        return self.get_one_item_from_cache(
            cache_key=cache_key,
            model=self.cache_model,
        )


@lru_cache()
def get_jwt_service() -> JWTService:
    return JWTService(
        cache=get_cache_db(),
        db=get_db(),
        db_model=models.RefreshToken,
    )
