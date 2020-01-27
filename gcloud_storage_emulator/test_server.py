import logging
import os
import sys
import unittest
from unittest import TestCase as BaseTestCase

import fs
import requests
from google.api_core.exceptions import Conflict, NotFound

from gcloud_storage_emulator.server import create_server
from gcloud_storage_emulator.settings import STORAGE_BASE, STORAGE_DIR


def _get_storage_client(http):
    """Gets a python storage client"""
    os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:9023"

    # Cloud storage uses environment variables to configure api endpoints for
    # file upload - which is read at module import time
    from google.cloud import storage
    return storage.Client(
        project="[PROJECT]",
        _http=http,
        client_options={"api_endpoint": "http://localhost:9023"},
    )


class BucketsTests(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls._server = create_server("localhost", 9023)
        cls._server.start()

    @classmethod
    def tearDownClass(cls):
        cls._server.stop()

    def setUp(self):
        BucketsTests._server.reset()
        self._session = requests.Session()
        self._client = _get_storage_client(self._session)

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


class ObjectsTests(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls._server = create_server("localhost", 9023)
        cls._server.start()

    @classmethod
    def tearDownClass(cls):
        cls._server.stop()

    def setUp(self):
        self._session = requests.Session()
        self._client = _get_storage_client(self._session)
        ObjectsTests._server.reset()

    def test_upload_from_string(self):
        content = "this is the content of the file\n"
        bucket = self._client.create_bucket("testbucket")
        blob = bucket.blob("testblob-name.txt")
        blob.upload_from_string(content)

        with fs.open_fs(STORAGE_BASE + STORAGE_DIR) as pwd:
            read_content = pwd.readtext("testbucket/testblob-name.txt")
            self.assertEqual(read_content, content)

    def test_upload_from_file(self):
        bucket = self._client.create_bucket("testbucket")
        blob = bucket.blob("README.md")
        with open("README.md", "rb") as file:
            blob.upload_from_file(file)

            with fs.open_fs(STORAGE_BASE + STORAGE_DIR) as pwd:
                read_content = pwd.readtext("testbucket/README.md")

        with open("README.md", "rb") as file:
            expected_content = str(file.read(), encoding="utf-8")
            self.assertEqual(read_content, expected_content)

    def test_get(self):
        file_name = "testblob-name.txt"
        content = "this is the content of the file\n"
        bucket = self._client.create_bucket("testbucket")
        blob = bucket.blob(file_name)
        blob.upload_from_string(content)

        blob = bucket.get_blob(file_name)
        self.assertEqual(blob.name, file_name)

    def test_get_nonexistant(self):
        bucket = self._client.create_bucket("testbucket")
        res = bucket.get_blob("idonotexist")

        self.assertIsNone(res)

        blob = bucket.blob("iexist")
        blob.upload_from_string("some_fake_content")
        blob = bucket.get_blob("idonotexist")

        self.assertIsNone(res)

    def test_download(self):
        content = "The quick brown fox jumps over the lazy dog\n"
        bucket = self._client.create_bucket("testbucket")

        blob = bucket.blob("iexist")
        blob.upload_from_string(content)

        blob = bucket.get_blob("iexist")
        fetched_content = blob.download_as_string()
        self.assertEqual(fetched_content, content.encode('utf-8'))


if __name__ == "__main__":
    root = logging.getLogger("")
    ch = logging.StreamHandler()
    root.addHandler(ch)
    root.setLevel(logging.DEBUG)
    sys.exit(unittest.main())
