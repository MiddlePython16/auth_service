from http import HTTPStatus
from typing import Optional

from core.settings import settings
from db.cache_db import get_cache_db
from flask import Response, request
from flask_jwt_extended import current_user
from schemas.base.responses import TOO_MANY_REQUESTS
from utils.utils import make_error_response

PIPE_EXPIRE_IN_SECONDS = 59


def rate_limit() -> Optional[Response]:
    if not settings.ENABLE_LIMITER:
        return None

    cache_db = get_cache_db()
    pipe = cache_db.pipeline()

    key = current_user.id if current_user else request.remote_addr

    pipe.incr(key, 1)
    pipe.expire(key, PIPE_EXPIRE_IN_SECONDS)

    pipe_result = pipe.execute()
    request_number = pipe_result[0]
    if request_number > settings.REQUEST_LIMIT_PER_MINUTE:
        return make_error_response(
            msg=TOO_MANY_REQUESTS,
            status=HTTPStatus.TOO_MANY_REQUESTS,
        )
