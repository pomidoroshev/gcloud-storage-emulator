import json
import logging
import re
import threading
import time
from http import server
from urllib.parse import parse_qs, urlparse

from gcloud_storage_emulator import settings
from gcloud_storage_emulator.handlers import buckets

logger = logging.getLogger("gcloud-storage-emulator")

GET = "GET"
POST = "POST"


HANDLERS = (
    (r"^/b$", {GET: buckets.get, POST: buckets.insert}),
)


def _read_data(request_handler):
    raw_data = request_handler.rfile.read(int(request_handler.headers['content-length']))

    if request_handler.headers['Content-Type'] == 'application/json':
        return json.loads(raw_data, encoding='utf-8')

    return raw_data


class Response(object):
    def __init__(self, handler, status=200):
        super().__init__()
        self._handler = handler
        self.status = status
        self._headers = {}
        self._content = ""

    def write(self, content):
        self._content += content
        # self._handler.wfile.write(content)

    def json(self, obj):
        self["Content-type"] = "application/json"
        self._content = json.dumps(obj)

    def __setitem__(self, key, value):
        self._headers[key] = value

    def __getitem__(self, key):
        return self._headers[key]

    def close(self):
        self._handler.send_response(self.status)
        for (k, v) in self._headers.items():
            self._handler.send_header(k, v)

        content = self._content.encode("utf-8")
        self._handler.send_header("Content-Lenght", str(len(content)))
        self._handler.end_headers()
        self._handler.wfile.write(content)


class Router(object):
    def __init__(self, request_handler):
        super().__init__()
        self._request_handler = request_handler
        self._path = request_handler.path
        self._url = urlparse(self._path)
        self._query = parse_qs(self._url.query)

    def handle(self, method):
        response = Response(self._request_handler)

        if not self._url.path.startswith(settings.API_ENDPOINT):
            response.status = 404
            response.close()
            return

        for regex, handlers in HANDLERS:
            pattern = re.compile(regex)
            match = pattern.fullmatch(self._url.path[len(settings.API_ENDPOINT):])
            if match:
                handler = handlers.get(method)

                handler({
                    "url": self._url,
                    "method": method,
                    "query": parse_qs(self._url.query),
                    "query_match": match,
                    "data": _read_data(self._request_handler)
                }, response)

                break
        else:
            response.status = 404
            return

        response.close()


class RequestHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        router = Router(self)
        router.handle(GET)

    def do_POST(self):
        router = Router(self)
        router.handle(POST)


class APIThread(threading.Thread):
    def __init__(self, host, port, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._host = host
        self._port = port
        self.is_running = threading.Event()
        self._httpd = None

    def run(self):
        self._httpd = server.HTTPServer((self._host, self._port), RequestHandler)
        self.is_running.set()
        self._httpd.serve_forever()

    def join(self, timeout=None):
        self.is_running.clear()
        if self._httpd:
            self._httpd.shutdown()
        logger.info("[API] Stopping API server")


class Server(object):
    def __init__(self, host, port):
        self._api = APIThread(host, port)

    def start(self):
        self._api.start()
        self._api.is_running.wait()  # Start the API thread

    def stop(self):
        self._api.join(timeout=1)

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
