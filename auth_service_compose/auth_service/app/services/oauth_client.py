from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Optional

from authlib.integrations.flask_client import OAuth
from extensions.oauth import get_google_client, get_oauth
from extensions.tracer import trace_decorator
from flask import url_for


class OauthServiceClient(ABC):

    @abstractmethod
    def get_client(self, **kwargs):  # noqa: WPS463
        pass  # noqa: WPS420

    @abstractmethod
    def register_redirect(self, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def login_redirect(self, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def get_user_data_from_token(self, **kwargs):  # noqa: WPS463
        pass  # noqa: WPS420


class GoogleOauthServiceClient(OauthServiceClient):
    @trace_decorator()
    def get_client(self, oauth: Optional[OAuth] = None, **kwargs):
        return get_google_client()

    @trace_decorator()
    def register_redirect(self, **kwargs):
        client = self.get_client()
        redirect_uri = url_for('oauth.oauth_register', provider='google', _external=True)
        return client.authorize_redirect(redirect_uri)

    @trace_decorator()
    def login_redirect(self, **kwargs):
        client = self.get_client()
        redirect_uri = url_for('oauth.oauth_login', provider='google', _external=True)
        return client.authorize_redirect(redirect_uri)

    @trace_decorator()
    def get_user_data_from_token(self, **kwargs):
        oauth = get_oauth()
        client = self.get_client(oauth=oauth)
        client.authorize_access_token()

        resp = client.get('userinfo')
        resp.json()

        user = oauth.google.userinfo()
        return (
            user['sub'],
            user['email'],
            user['email'].split('@')[0],
        )


@lru_cache()
def get_google_oauth_client_service(
) -> GoogleOauthServiceClient:
    return GoogleOauthServiceClient()
