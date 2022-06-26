# Python Code Wake V1 WSGI Werkzeug middleware (pycodewake-v1wsgi-service)

[![test](https://github.com/mwri/pycodewake-v1wsgi-service/actions/workflows/test.yml/badge.svg)](https://github.com/mwri/pycodewake-v1wsgi-service/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/mwri/pycodewake-v1wsgi-service/branch/main/graph/badge.svg)](https://codecov.io/gh/mwri/pycodewake-v1wsgi-service)

This store adapter provides a WSGI Werkzeug middleware which provides an implementation of the V1 REST API service.

For example:

```python
import flask
from code_wake_v1wsgi_service import V1WsgiMiddleware
from code_wake_sql14_store import Sql14Store

flask_app = flask.Flask(__name__)
flask_app.wsgi_app = V1WsgiMiddleware(flask_app.wsgi_app, "/some/v1/code_wake/path", Sql14Store("sqlite:///:memory:"))
```

Here, a flask server is created, and the middleware added to it. The parameters for the middleware are
the URL base path (on top of which `/processes`, `/events` and any other restful resources will be
added) and the back end store.

A remote process may then use the `code-wake-v1rest-store` Code Wake store adapter, and via this
middleware, communicate to the back end store provided.

No authentication is provided by the middleware.
