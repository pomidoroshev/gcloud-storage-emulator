import email
import json
import logging
import re
import threading
import time
from functools import partial
from http import server, HTTPStatus
from urllib.parse import parse_qs, urlparse

from gcloud_storage_emulator import settings
from gcloud_storage_emulator.handlers import buckets, objects
from gcloud_storage_emulator.storage import Storage

logger = logging.getLogger("gcloud-storage-emulator")

GET = "GET"
POST = "POST"
DELETE = "DELETE"

HANDLERS = (
    (r"^{}/b$".format(settings.API_ENDPOINT), {GET: buckets.ls, POST: buckets.insert}),
    (r"^{}/b/(?P<bucket_name>[-\w]+)$".format(settings.API_ENDPOINT), {GET: buckets.get, DELETE: buckets.delete}),
    (r"^{}/b/(?P<bucket_name>[-\w]+)/o$".format(settings.UPLOAD_API_ENDPOINT), {POST: objects.insert}),
    (r"^{}/b/(?P<bucket_name>[-\w]+)/o/(?P<object_id>[-.\w]+)$".format(settings.API_ENDPOINT), {GET: objects.get}),
    (
        r"^{}/b/(?P<bucket_name>[-\w]+)/o/(?P<object_id>[-.\w]+)$".format(settings.DOWNLOAD_API_ENDPOINT),
        {GET: objects.download},
    ),
)


def _read_data(request_handler):
    if not request_handler.headers["Content-Length"] or not request_handler.headers["Content-Type"]:
        return None

    raw_data = request_handler.rfile.read(int(request_handler.headers["Content-Length"]))

    content_type = request_handler.headers["Content-Type"]

    if content_type == "application/json":
        return json.loads(raw_data, encoding="utf-8")

    if content_type.startswith("multipart/"):
        content = "Content-Type:" + content_type + "\r\n"
        content += raw_data.decode("utf-8")
        msg = email.message_from_string(content)

        payload = msg.get_payload()

        # For multipart upload, google API expect the first item to be a json-encoded
        # object, and the second (and only other) part, the file content
        return {
            "meta": json.loads(payload[0].get_payload(), encoding="utf-8"),
            "content": payload[1].get_payload(),
            "content-type": payload[1].get_content_type(),
        }

    return raw_data


class Request(object):
    def __init__(self, request_handler, method):
        super().__init__()
        self._path = request_handler.path
        self._request_handler = request_handler
        self._server_address = request_handler.server.server_address
        self._base_url = "http://{}:{}".format(self._server_address[0], self._server_address[1])
        self._full_url = self._base_url + self._path
        self._parsed_url = urlparse(self._full_url)
        self._query = parse_qs(self._parsed_url.query)
        self._methtod = method
        self._data = None

    @property
    def path(self):
        return self._parsed_url.path

    @property
    def base_url(self):
        return self._base_url

    @property
    def full_url(self):
        return self._full_url

    @property
    def method(self):
        return self._methtod

    @property
    def query(self):
        return self._query

    @property
    def params(self):
        return self._match.groupdict() if self._match else None

    @property
    def data(self):
        if not self._data:
            self._data = _read_data(self._request_handler)
        return self._data

    def set_match(self, match):
        self._match = match


class Response(object):
    def __init__(self, handler):
        super().__init__()
        self._handler = handler
        self.status = HTTPStatus.OK
        self._headers = {}
        self._content = ""

    def write(self, content):
        logger.warning("[RESPONSE] Content handled as string, should be handled as stream")
        self._content += content

    def write_file(self, content, content_type="application/octet-stream"):
        if content_type is not None:
            self["Content-type"] = content_type

        self._content = content

    def json(self, obj):
        self["Content-type"] = "application/json"
        self._content = json.dumps(obj)

    def __setitem__(self, key, value):
        self._headers[key] = value

    def __getitem__(self, key):
        return self._headers[key]

    def close(self):
        self._handler.send_response(self.status.value, self.status.phrase)
        for (k, v) in self._headers.items():
            self._handler.send_header(k, v)

        content = self._content

        if isinstance(self._content, str):
            content = self._content.encode("utf-8")

        self._handler.send_header("Content-Lenght", str(len(content)))
        self._handler.end_headers()
        self._handler.wfile.write(content)


class Router(object):
    def __init__(self, request_handler):
        super().__init__()
        self._request_handler = request_handler

    def handle(self, method):
        request = Request(self._request_handler, method)
        response = Response(self._request_handler)

        for regex, handlers in HANDLERS:
            pattern = re.compile(regex)
            match = pattern.fullmatch(request.path)
            if match:
                request.set_match(match)
                handler = handlers.get(method)
                try:
                    handler(request, response, self._request_handler.storage)
                except Exception as e:
                    logger.error("An error has occured while running the handler for {}".format(request.full_url))
                    logger.error(e)
                    raise e
                break
        else:
            logger.error("Method not implemented: {} - {}".format(request.method, request.path))
            logger.error(request)
            response.status = HTTPStatus.NOT_IMPLEMENTED

        response.close()


class RequestHandler(server.BaseHTTPRequestHandler):
    def __init__(self, storage, *args, **kwargs):
        self.storage = storage
        super().__init__(*args, **kwargs)

    def do_GET(self):
        router = Router(self)
        router.handle(GET)

    def do_POST(self):
        router = Router(self)
        router.handle(POST)

    def do_DELETE(self):
        router = Router(self)
        router.handle(DELETE)


class APIThread(threading.Thread):
    def __init__(self, host, port, storage, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._host = host
        self._port = port
        self.is_running = threading.Event()
        self._httpd = None
        self._storage = storage

    def run(self):
        self._httpd = server.HTTPServer((self._host, self._port), partial(RequestHandler, self._storage))
        self.is_running.set()
        self._httpd.serve_forever()

    def join(self, timeout=None):
        self.is_running.clear()
        if self._httpd:
            logger.info("[API] Stopping API server")
            self._httpd.shutdown()
            self._httpd.server_close()


class Server(object):
    def __init__(self, host, port):
        self._storage = Storage()
        self._api = APIThread(host, port, self._storage)

    def start(self):
        self._api.start()
        self._api.is_running.wait()  # Start the API thread

    def stop(self):
        self._api.join(timeout=1)

    def reset(self):
        self._storage.reset()

    def run(self):
        try:
            self.start()
            logger.info("[SERVER] All services started")

            while True:
                try:
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    logger.info("[SERVER] Received keyboard interrupt")
                    break

        finally:
            self.stop()


def create_server(host, port):
    logger.info("Starting server at {}:{}".format(host, port))
    return Server(host, port)
