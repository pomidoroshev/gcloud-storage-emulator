import unittest
from unittest import TestCase as BaseTestCase

from server import create_server

from google.cloud import storage
import google.cloud.storage._http
import time
import requests
import os

class TestCase(BaseTestCase):
    def setUp(self):
        self._server = create_server("localhost", 9023)
        self._server.start()
        time.sleep(1)
        self._session = requests.Session()
        self._client = storage.Client(project='[PROJECT]', _http=self._session, client_options={ 'api_endpoint': "http://localhost:9023"})

    def tearDown(self):
        self._server.stop()

    def test_something(self):
        ret = self._client.create_bucket('bucket_name')
        print(ret.__dict__)


if __name__ == '__main__':
    unittest.main()
