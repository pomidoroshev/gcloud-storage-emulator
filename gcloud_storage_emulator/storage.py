import datetime
import logging
import json

import fs
from fs.errors import FileExpected, ResourceNotFound

from gcloud_storage_emulator.exceptions import NotFound
from gcloud_storage_emulator.settings import STORAGE_BASE, STORAGE_DIR

logger = logging.getLogger("storage")


class Storage(object):
    buckets = {}

    def __init__(self):
        self._pwd = fs.open_fs(STORAGE_BASE)
        try:
            self._fs = self._pwd.makedir(STORAGE_DIR)
        except fs.errors.DirectoryExists:
            self._fs = self._pwd.opendir(STORAGE_DIR)

        self._read_config_from_file()

    def _write_config_to_file(self):
        data = {
            "buckets": self.buckets,
            "objects": self.objects,
            "resumable": self.resumable,
        }

        with self._fs.open(".meta", mode="w") as meta:
            json.dump(data, meta, indent=2)

    def _read_config_from_file(self):
        try:
            with self._fs.open(".meta", mode="r") as meta:
                data = json.load(meta)
                self.buckets = data.get("buckets")
                self.objects = data.get("objects")
                self.resumable = data.get("resumable")
        except ResourceNotFound:
            self.buckets = {}
            self.objects = {}
            self.resumable = {}

    def _get_or_create_bucket_dir(self, bucket_name):
        try:
            bucket_dir = self._fs.makedir(bucket_name)
        except fs.errors.DirectoryExists:
            bucket_dir = self._fs.opendir(bucket_name)

        return bucket_dir

    def create_file(self, bucket_name, file_name, content, file_obj):
        bucket_dir = self._get_or_create_bucket_dir(bucket_name)

        with bucket_dir.open(file_name, mode="w") as file:
            file.write(content)
            bucket_objects = self.objects.get(bucket_name, {})
            bucket_objects[file_name] = file_obj
            self.objects[bucket_name] = bucket_objects
            self._write_config_to_file()

    def create_resumable_upload(self, bucket_name, file_name, file_obj):
        file_id = "{}:{}:{}".format(bucket_name, file_name, datetime.datetime.now())
        self.resumable[file_id] = file_obj
        self._write_config_to_file()
        return file_id

    def create_file_for_resumable_upload(self, file_id, content):
        file_obj = self.resumable[file_id]
        bucket_name = file_obj["bucket"]
        file_name = file_obj["name"]
        bucket_dir = self._get_or_create_bucket_dir(bucket_name)

        with bucket_dir.open(file_name, mode="wb") as file:
            file.write(content)

        file_obj["size"] = str(len(content))
        bucket_objects = self.objects.get(bucket_name, {})
        bucket_objects[file_name] = file_obj
        self.objects[bucket_name] = bucket_objects
        del self.resumable[file_id]
        self._write_config_to_file()

        return file_obj

    def get_file_obj(self, bucket_name, file_name):
        try:
            return self.objects[bucket_name][file_name]
        except KeyError:
            raise NotFound

    def get_file(self, bucket_name, file_name):
        try:
            bucket_dir = self._fs.opendir(bucket_name)
            return bucket_dir.open(file_name, mode="rb").read()
        except (FileExpected, ResourceNotFound) as e:
            logger.error("Resource not found:")
            logger.error(e)
            raise NotFound

    def reset(self):
        self.buckets = {}
        self.objects = {}
        self.resumable = {}

        try:
            self._fs.remove('.meta')
            for path in self._fs.listdir('.'):
                self._fs.removetree(path)
        except ResourceNotFound as e:
            logger.warning("Resource not found:")
            logger.warning(e)
