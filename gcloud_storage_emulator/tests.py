import logging
import sys
import unittest
from unittest import TestCase as BaseTestCase

import requests
from google.api_core.exceptions import Conflict, NotFound
from google.cloud import storage

from server import create_server


class BucketTests(BaseTestCase):
    def setUp(self):
        self._server = create_server("localhost", 9023)
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

    def test_bucket_creation_no_override(self):
        self._client.create_bucket('bucket_name')
        with self.assertRaises(Conflict):
            self._client.create_bucket('bucket_name')

    def test_bucket_list(self):
        bucket = self._client.create_bucket('bucket_name')
        all_bucket_names = [bucket.name for bucket in self._client.list_buckets()]
        self.assertIn(bucket.name, all_bucket_names)

    def test_bucket_get_existing(self):
        bucket = self._client.create_bucket('bucket_name')
        fetched_bucket = self._client.get_bucket('bucket_name')
        self.assertEqual(fetched_bucket.name, bucket.name)

    def test_bucket_get_non_existing(self):
        with self.assertRaises(NotFound):
            self._client.get_bucket('bucket_name')

    def test_bucket_delete(self):
        bucket = self._client.create_bucket('bucket_name')
        bucket.delete()

    def test_bucket_delete_non_existing(self):
        # client.bucket doesn't create the actual bucket resource remotely,
        # it only instantiate it in the local client
        bucket = self._client.bucket('bucket_name')
        with self.assertRaises(NotFound):
            bucket.delete()

    # TODO: test delete non-empty bucket and delete-force


if __name__ == '__main__':
    root = logging.getLogger('')
    ch = logging.StreamHandler()
    root.addHandler(ch)
    root.setLevel(logging.DEBUG)
    sys.exit(unittest.main())
