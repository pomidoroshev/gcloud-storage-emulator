import os
from io import BytesIO
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
        cls._server = create_server("localhost", 9023, in_memory=False)
        cls._server.start()

    @classmethod
    def tearDownClass(cls):
        cls._server.stop()

    def setUp(self):
        BucketsTests._server.wipe()
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

        with self.assertRaises(NotFound):
            self._client.get_bucket('bucket_name')

    def test_bucket_delete_removes_file(self):
        bucket = self._client.create_bucket('bucket_name')
        bucket.delete()

        with fs.open_fs(STORAGE_BASE + STORAGE_DIR) as pwd:
            self.assertFalse(pwd.exists('bucket_name'))

    def test_bucket_delete_non_existing(self):
        # client.bucket doesn't create the actual bucket resource remotely,
        # it only instantiate it in the local client
        bucket = self._client.bucket('bucket_name')
        with self.assertRaises(NotFound):
            bucket.delete()

    def test_bucket_delete_non_empty(self):
        bucket = self._client.create_bucket('bucket_name')
        blob = bucket.blob("canttouchme.txt")
        blob.upload_from_string('This should prevent deletion if not force')

        with self.assertRaises(Conflict):
            bucket.delete()

        blob = bucket.blob("canttouchme.txt")
        self.assertIsNotNone(blob)

    # TODO: test delete-force


class ObjectsTests(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls._server = create_server("localhost", 9023, in_memory=False)
        cls._server.start()

    @classmethod
    def tearDownClass(cls):
        cls._server.stop()

    def setUp(self):
        self._session = requests.Session()
        self._client = _get_storage_client(self._session)
        ObjectsTests._server.wipe()

    def test_upload_from_string(self):
        content = "this is the content of the file\n"
        bucket = self._client.create_bucket("testbucket")
        blob = bucket.blob("testblob-name.txt")
        blob.upload_from_string(content)

        with fs.open_fs(STORAGE_BASE + STORAGE_DIR) as pwd:
            read_content = pwd.readtext("testbucket/testblob-name.txt")
            self.assertEqual(read_content, content)

    def test_upload_from_text_file(self):
        text_test = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_text.txt')
        bucket = self._client.create_bucket("testbucket")
        blob = bucket.blob("test_text.txt")
        with open(text_test, "rb") as file:
            blob.upload_from_file(file)

            with fs.open_fs(STORAGE_BASE + STORAGE_DIR) as pwd:
                read_content = pwd.readtext("testbucket/test_text.txt")

        with open(text_test, "rb") as file:
            expected_content = str(file.read(), encoding="utf-8")
            self.assertEqual(read_content, expected_content)

    def test_upload_from_bin_file(self):
        test_binary = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_binary.png')
        bucket = self._client.create_bucket("testbucket")
        blob = bucket.blob("binary.png")
        with open(test_binary, "rb") as file:
            blob.upload_from_file(file)

        with fs.open_fs(STORAGE_BASE + STORAGE_DIR) as pwd:
            read_content = pwd.readbytes("testbucket/binary.png")

        with open(test_binary, "rb") as file:
            expected_content = file.read()
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

    def test_download_as_string(self):
        content = "The quick brown fox jumps over the lazy dog\n"
        bucket = self._client.create_bucket("testbucket")

        blob = bucket.blob("iexist")
        blob.upload_from_string(content)

        blob = bucket.get_blob("iexist")
        fetched_content = blob.download_as_string()
        self.assertEqual(fetched_content, content.encode('utf-8'))

    def test_download_binary_to_file(self):
        test_binary = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_binary.png')
        bucket = self._client.create_bucket("testbucket")

        blob = bucket.blob("binary.png")
        with open(test_binary, "rb") as file:
            blob.upload_from_file(file, content_type="image/png")

        blob = bucket.get_blob("binary.png")
        fetched_file = BytesIO()
        blob.download_to_file(fetched_file)

        with open(test_binary, "rb") as file:
            self.assertEqual(fetched_file.getvalue(), file.read())

    def test_download_text_to_file(self):
        test_text = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_text.txt')
        bucket = self._client.create_bucket("testbucket")

        blob = bucket.blob("text.txt")
        with open(test_text, "rb") as file:
            blob.upload_from_file(file, content_type="text/plain; charset=utf-8")

        blob = bucket.get_blob("text.txt")
        fetched_file = BytesIO()
        blob.download_to_file(fetched_file)

        with open(test_text, "rb") as file:
            self.assertEqual(fetched_file.getvalue(), file.read())
