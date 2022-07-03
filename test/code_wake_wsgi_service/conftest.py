"""Pytest configuration / fixtures."""


import flask
import flask.testing
import pytest
from code_wake.test.conftest import *
from code_wake_sql14_store import Sql14Store
from code_wake_v1rest_store import V1RestStore

from code_wake_v1wsgi_service import V1WsgiMiddleware


@pytest.fixture
def store_params():
    def params():
        flask_app = flask.Flask(__name__)
        flask_app.wsgi_app = V1WsgiMiddleware(flask_app.wsgi_app, "/abc", Sql14Store("sqlite:///:memory:"))

        return (["/abc"], {"flask_app": flask_app})

    return params


@pytest.fixture
def store_cls():
    class TestV1RestStore(V1RestStore):
        def __init__(self, *args, flask_app, **kwargs):
            super().__init__(*args, **kwargs)

            self._flask_app = flask_app
            flask_app.test_client_class = self.FlaskClient

        class FlaskClient(flask.testing.FlaskClient):
            def open(self, *args, **kwargs):
                headers = kwargs.setdefault("headers", {})
                headers.setdefault("content-type", "application/json")
                return super().open(*args, **kwargs)

        @property
        def session(self):
            return self._flask_app.test_client

    return TestV1RestStore


@pytest.fixture
def store_cleanup():
    return lambda store: None
