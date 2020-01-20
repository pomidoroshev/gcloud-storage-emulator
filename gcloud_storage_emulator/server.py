
from datetime import datetime
import logging
import sys
import time
import threading
import grpc
from concurrent import futures
from http import server


logger = logging.getLogger("gcloud-storage-emulator")

class RequestHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        print('Doing GET!')

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write('{ "projectNumber": 1234 }'.encode("utf8"))
        print('Doing POST')


class APIThread(threading.Thread):
    def __init__(self, host, port, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._host = host
        self._port = port
        self._is_running = threading.Event()
        self._httpd = None

    def run(self):
        self._httpd = server.HTTPServer((self._host, self._port), RequestHandler)
        self._httpd.serve_forever()

    def join(self, timeout=None):
        self._is_running.clear()
        if self._httpd:
            self._httpd.shutdown()
        logger.info("[API] Stopping API server")


class Server(object):
    def __init__(self, host, port):
        self._api = APIThread(host, port)

    def start(self):
        self._api.start()  # Start the API thread

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
                    break

        finally:
            self.stop()

def create_server(host, port):
    return Server(host, port)
