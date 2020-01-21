import logging
import requests
import unittest

from google.cloud import storage
from server import create_server
from unittest import TestCase as BaseTestCase


class TestCase(BaseTestCase):
    def setUp(self):
        self._server = create_server("localhost", 9023)
        self._server.start()
        self._session = requests.Session()
        self._client = storage.Client(project='[PROJECT]', _http=self._session, client_options={ 'api_endpoint': "http://localhost:9023"})

    def tearDown(self):
        self._server.stop()

    def test_something(self):
        ret = self._client.create_bucket('bucket_name')
        self.assertEqual(ret.project_number, 1234)


if __name__ == '__main__':
    root = logging.getLogger('')
    ch = logging.StreamHandler()
    root.addHandler(ch)
    root.setLevel(logging.WARNING)
    unittest.main()
