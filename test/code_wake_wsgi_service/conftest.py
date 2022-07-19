"""Pytest configuration / fixtures."""


import flask
import flask.testing
import pytest
from code_wake.test.conftest import *
from code_wake_sql14_store import Sql14Store
from code_wake_v1rest_store import V1RestStore
from requests_flask_adapter import Session

from code_wake_v1wsgi_service import V1WsgiMiddleware


@pytest.fixture
def store_params():
    def params():
        flask_app = flask.Flask(__name__)
        flask_app.wsgi_app = V1WsgiMiddleware(flask_app.wsgi_app, "", Sql14Store("sqlite:///:memory:"))

        Session.register("http://", flask_app)

        return (["http://abc"], {"session": Session()})

    return params


@pytest.fixture
def store_cls():
    class TestV1RestStore(V1RestStore):
        def __init__(self, *args, session, **kwargs):
            super().__init__(*args, **kwargs)

            self._session = session

        def session(self):
            return self._session

    return TestV1RestStore


@pytest.fixture
def store_cleanup():
    return lambda store: None
