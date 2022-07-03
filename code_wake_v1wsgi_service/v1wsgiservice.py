"""V1 REST API middleware module."""

import binascii
import json
import urllib
from datetime import datetime

import werkzeug


class V1WsgiMiddleware:
    def __init__(self, next_app, path: str, store):
        self._next_app = next_app
        self._path = path
        self._store = store
        self._json_encoder = json.JSONEncoder()
        self._json_decoder = json.JSONDecoder()

    def __call__(self, environ, start_response):
        request = werkzeug.wrappers.Request(environ)

        if request.path.startswith(self._path):
            path_postfix = request.path[len(self._path) :]

            if path_postfix == "" or path_postfix[0] == "/":
                return self._service_request(request, path_postfix)(environ, start_response)

        return self._next_app(environ, start_response)

    def _service_request(self, request, path_postfix):
        if request.method == "POST":
            if "content-type" not in request.headers or "application/json" not in request.headers["content-type"]:
                return self.error_response(
                    400,
                    "application/json content type only supported",
                )

        if path_postfix.startswith("/environments/"):
            path_postfix = path_postfix[len("/environments") :]

            if request.method == "GET" and len(path_postfix) > 1 and path_postfix[0] == "/":
                return self.get_environment_by_id(request, path_postfix[1:])
            else:
                return self.error_response(
                    405,
                    "method not allowed",
                )

        elif path_postfix.startswith("/apps"):
            path_postfix = path_postfix[len("/apps") :]

            if path_postfix == "" or path_postfix == "/":
                if request.method == "POST":
                    return self.insert_app(
                        request,
                    )
                else:
                    return self.error_response(
                        405,
                        "method not allowed",
                    )
            elif len(path_postfix) > 1 and path_postfix[0] == "/":
                if request.method == "GET":
                    return self.get_app_by_id(request, path_postfix[1:])
                else:
                    return self.error_response(
                        405,
                        "method not allowed",
                    )

        elif path_postfix.startswith("/app_vsns"):
            path_postfix = path_postfix[len("/app_vsns") :]

            if request.method == "GET" and len(path_postfix) > 1 and path_postfix[0] == "/":
                return self.get_app_vsn_by_id(request, path_postfix[1:])
            else:
                return self.error_response(
                    405,
                    "method not allowed",
                )

        elif path_postfix.startswith("/processes"):
            path_postfix = path_postfix[len("/processes") :]

            if path_postfix == "" or path_postfix == "/":
                if request.method == "POST":
                    return self.insert_process(
                        request,
                    )
                else:
                    return self.error_response(
                        405,
                        "method not allowed",
                    )
            elif len(path_postfix) > 1 and path_postfix[0] == "/":
                if request.method == "GET":
                    return self.get_process_by_id(
                        request,
                        path_postfix[1:],
                    )
                else:
                    return self.error_response(
                        405,
                        "method not allowed",
                    )

        elif path_postfix.startswith("/events"):
            path_postfix = path_postfix[len("/events") :]

            if path_postfix == "" or path_postfix == "/":
                if request.method == "POST":
                    return self.insert_event(
                        request,
                    )
                elif request.method == "GET":
                    return self.get_events_by_data(
                        request,
                    )
                else:
                    return self.error_response(
                        405,
                        "method not allowed",
                    )

        return self.error_response(404, "not found")

    def error_response(self, status_code, msg):
        return werkzeug.wrappers.Response(
            self._json_encoder.encode({"error": msg}),
            mimetype="application/json",
            status=status_code,
        )

    def insert_app(self, request):
        json_body = self._json_decoder.decode(request.data.decode())

        if "name" not in json_body:
            return self.error_response(400, "no name in post data")

        name = json_body["name"]
        vsn = json_body.get("vsn")
        app = self._store.insert_app(name, vsn)

        if app is None:
            return self.error_response(404, "app not found")

        return werkzeug.wrappers.Response(
            self._json_encoder.encode({"id": app.id, "name": name, "vsn": vsn}),
            mimetype="application/json",
            status=201,
        )

    def get_environment_by_id(self, request, str_environment_id):
        environment_record = self._store.get_environment_by_id(int(str_environment_id))

        if environment_record is None:
            return self.error_response(404, "environment not found")

        return werkzeug.wrappers.Response(
            self._json_encoder.encode(
                {
                    "id": environment_record.id,
                    "name": environment_record.name,
                }
            ),
            mimetype="application/json",
            status=200,
        )

    def get_app_by_id(self, request, str_app_id):
        app_record = self._store.get_app_by_id(int(str_app_id))

        if app_record is None:
            return self.error_response(404, "app not found")

        return werkzeug.wrappers.Response(
            self._json_encoder.encode(
                {
                    "id": app_record.id,
                    "name": app_record.name,
                }
            ),
            mimetype="application/json",
            status=200,
        )

    def get_app_vsn_by_id(self, request, str_app_vsn_id):
        app_vsn_record = self._store.get_app_vsn_by_id(int(str_app_vsn_id))

        if app_vsn_record is None:
            return self.error_response(404, "app_vsn not found")

        return werkzeug.wrappers.Response(
            self._json_encoder.encode(
                {
                    "id": app_vsn_record.id,
                    "vsn": app_vsn_record.vsn,
                }
            ),
            mimetype="application/json",
            status=200,
        )

    def get_process_by_id(self, request, str_process_id):
        process = self._store.get_process_by_id(int(str_process_id))

        if process is None:
            return self.error_response(404, "process not found")

        return werkzeug.wrappers.Response(
            self._json_encoder.encode(
                {
                    "id": process.id,
                    "run_ts": process.run_ts,
                    "environment_id": process.environment_id,
                    "app_id": process.app_id,
                    "app_vsn_id": process.app_vsn_id,
                    "pid": process.pid,
                    "username": process.username,
                    "fqdn": process.fqdn,
                    "exe_path": process.exe_path,
                }
            ),
            mimetype="application/json",
            status=200,
        )

    def insert_process(self, request):
        json = self._json_decoder.decode(request.data.decode())

        for key in ("pid", "username", "fqdn", "exe_path"):
            if key not in json:
                return self.error_response(400, f"no {key} in post data")

        unstored_process = self.Process(
            environment=None if json.get("environment") is None else self.Environment(name=json["environment"]),
            pid=json["pid"],
            username=json["username"],
            fqdn=json["fqdn"],
            exe_path=json["exe_path"],
            app=None if json.get("app") is None else self.App(name=json["app"]),
            app_vsn=None if json.get("app_vsn") is None else self.AppVsn(vsn=json["app_vsn"]),
        )

        process = self._store.insert_process(unstored_process)

        return werkzeug.wrappers.Response(
            self._json_encoder.encode(
                {
                    "id": process.id,
                    "run_ts": process.run_ts,
                    "environment_id": process.environment_id,
                    "app_id": process.app_id,
                    "app_vsn_id": process.app_vsn_id,
                    "pid": process.pid,
                    "username": process.username,
                    "fqdn": process.fqdn,
                    "exe_path": process.exe_path,
                }
            ),
            mimetype="application/json",
            status=201,
        )

    def insert_event(self, request):
        params = urllib.parse.parse_qsl(request.query_string.decode())
        sync = ("sync", "true") in params
        json = self._json_decoder.decode(request.data.decode())

        process = self._store.get_process_by_id(json["process_id"])

        if process is None:
            return self.error_response(404, "process not found")

        event = self._store.insert_event(
            process,
            json["data"],
            inc_st=json["stacktrace"] is not None,
            st_data=json["stacktrace"],
            sync=sync,
        )

        if sync:
            return werkzeug.wrappers.Response(
                self._json_encoder.encode(
                    {
                        "id": event.id,
                        "when_ts": event.when_ts,
                        "process_id": process.id,
                        "digest": None if event.digest is None else binascii.b2a_hex(event.digest).decode(),
                        "stacktrace": None
                        if event.stacktrace is None
                        else {
                            "id": event.stacktrace.id,
                            "digest": binascii.b2a_hex(event.stacktrace.digest).decode(),
                            "stackframes": [[sf.filename, sf.lineno, sf.src] for sf in event.stacktrace.stackframes],
                        },
                    }
                ),
                mimetype="application/json",
                status=201,
            )
        else:
            return werkzeug.wrappers.Response("", status=202)

    def get_events_by_data(self, request):
        params = urllib.parse.parse_qsl(request.query_string.decode())
        where = [tuple(clause.split("=", 1)) for clause in dict(params)["where"].split(",")]

        events = self._store.get_events_by_data(where)

        return werkzeug.wrappers.Response(
            self._json_encoder.encode(
                [
                    {
                        "id": event.id,
                        "when_ts": event.when_ts,
                        "process_id": event.process_id,
                        "digest": None if event.digest is None else binascii.b2a_hex(event.digest).decode(),
                        "data": [[ed.key, ed.val] for ed in event.data],
                        "stacktrace": None
                        if event.stacktrace is None
                        else {
                            "id": event.stacktrace.id,
                            "digest": binascii.b2a_hex(event.stacktrace.digest).decode(),
                            "stackframes": [[sf.filename, sf.lineno, sf.src] for sf in event.stacktrace.stackframes],
                        },
                    }
                    for event in events
                ]
            ),
            mimetype="application/json",
            status=201,
        )

    class Base:
        pass

    class Environment(Base):
        def __init__(self, id=None, name=None):
            self.id = id
            self.name = name

        def __repr__(self):
            return f"<V1WsgiMiddleware.Environment(id='{self.id}')>"

    class Process(Base):
        def __init__(
            self,
            id=None,
            run_ts=None,
            environment=None,
            pid=None,
            username=None,
            fqdn=None,
            exe_path=None,
            app=None,
            app_vsn=None,
        ):
            self.id = id
            self.run_ts = datetime.now().timestamp()
            self.environment = environment
            self.pid = pid
            self.username = username
            self.fqdn = fqdn
            self.exe_path = exe_path
            self.app = app
            self.app_vsn = app_vsn

    class App(Base):
        def __init__(self, id=None, name=None):
            self.id = id
            self.name = name

        def __repr__(self):
            return f"<V1WsgiMiddleware.App(id='{self.id}')>"

    class AppVsn(Base):
        def __init__(self, id=None, vsn=None):
            self.id = id
            self.vsn = vsn

    def __repr__(self):
        return f"<V1WsgiMiddleware.AppVsn(id='{self.id}')>"
