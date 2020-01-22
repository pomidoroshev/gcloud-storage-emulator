import logging
import sys
import unittest
from unittest import TestCase as BaseTestCase

import requests
from google.cloud import storage

from server import create_server


class ServerTests(BaseTestCase):
    def setUp(self):
        self._server = create_server("localhost", 9023)
        print("SETUP")
        self._server.start()
        self._session = requests.Session()
        self._client = storage.Client(
            project='[PROJECT]',
            _http=self._session,
            client_options={'api_endpoint': "http://localhost:9023"},
        )

    def tearDown(self):
        self._server.stop()

    def test_bucket_creation(self):
        bucket = self._client.create_bucket('bucket_name')
        self.assertEqual(bucket.project_number, 1234)

    def test_bucket_list(self):
        bucket = self._client.create_bucket('bucket_name')
        self.assertIn(bucket, self._client.list_buckets())


if __name__ == '__main__':
    root = logging.getLogger('')
    ch = logging.StreamHandler()
    root.addHandler(ch)
    root.setLevel(logging.DEBUG)
    sys.exit(unittest.main())
