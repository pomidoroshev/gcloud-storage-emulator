import datetime
import logging
import json

import fs
from fs.errors import FileExpected, ResourceNotFound

from gcloud_storage_emulator.exceptions import NotFound
from gcloud_storage_emulator.settings import STORAGE_BASE, STORAGE_DIR

logger = logging.getLogger("storage")


class Storage(object):
    def __init__(self, use_memory_fs=False):
        self._use_memory_fs = use_memory_fs
        self._pwd = fs.open_fs(self.get_storage_base())
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

    def get_storage_base(self):
        """Returns the pyfilesystem-compatible fs path to the storage

        This is the OSFS if using disk storage, or "mem://" otherwise.
        See https://docs.pyfilesystem.org/en/latest/guide.html#opening-filesystems for more info

        Returns:
            string -- The relevant filesystm
        """

        if self._use_memory_fs:
            return "mem://"
        else:
            return STORAGE_BASE

    def get_bucket(self, bucket_name):
        """Get the bucket resourec object given the bucket name

        Arguments:
            bucket_name {str} -- Name of the bucket

        Returns:
            dict -- GCS-like Bucket resource
        """

        return self.buckets.get(bucket_name)

    def create_bucket(self, bucket_name, bucket_obj):
        """Create a bucket object representation and save it to the current fs

        Arguments:
            bucket_name {str} -- Name of the GCS bucket
            bucket_obj {dict} -- GCS-like Bucket resource

        Returns:
            [type] -- [description]
        """

        self.buckets[bucket_name] = bucket_obj
        self._write_config_to_file()
        return bucket_obj

    def create_file(self, bucket_name, file_name, content, file_obj):
        """Create a text file given a string content

        Arguments:
            bucket_name {str} -- Name of the bucket to save to
            file_name {str} -- File name used to store data
            content {str} -- Content of the file to write
            file_obj {dict} -- GCS-like Object resource
        """

        bucket_dir = self._get_or_create_bucket_dir(bucket_name)

        with bucket_dir.open(file_name, mode="w") as file:
            file.write(content)
            bucket_objects = self.objects.get(bucket_name, {})
            bucket_objects[file_name] = file_obj
            self.objects[bucket_name] = bucket_objects
            self._write_config_to_file()

    def create_resumable_upload(self, bucket_name, file_name, file_obj):
        """Initiate the necessary data to support partial upload.

        This doesn't fully support partial upload, but expect the secondary PUT
        call to send all the data in one go.

        Basically, we try to comply to the bare minimum to the API described in
        https://cloud.google.com/storage/docs/performing-resumable-uploads ignoring
        any potential network failures

        Arguments:
            bucket_name {string} -- Name of the bucket to save to
            file_name {string} -- File name used to store data
            file_obj {dict} -- GCS Object resource

        Returns:
            str -- id of the resumable upload session (`upload_id`)
        """

        file_id = "{}:{}:{}".format(bucket_name, file_name, datetime.datetime.now())
        self.resumable[file_id] = file_obj
        self._write_config_to_file()
        return file_id

    def create_file_for_resumable_upload(self, file_id, content):
        """Create a binary file following a partial upload request

        This also updates the meta with the final file-size

        Arguments:
            file_id {str} -- the `upload_id` of the partial upload session
            content {bytes} -- raw content to add to the file

        Returns:
            dict -- GCS-like Object resource
        """

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
        """Gets the meta information for a file within a bucket

        Arguments:
            bucket_name {str} -- Name of the bucket
            file_name {str} -- File name

        Raises:
            NotFound: Raised when the object doesn't exist

        Returns:
            dict -- GCS-like Object resource
        """

        try:
            return self.objects[bucket_name][file_name]
        except KeyError:
            raise NotFound

    def get_file(self, bucket_name, file_name):
        """Get the raw data of a file within a bucket

        Arguments:
            bucket_name {str} -- Name of the bucket
            file_name {str} -- File name

        Raises:
            NotFound: Raised when the object doesn't exist

        Returns:
            bytes -- Raw content of the file
        """

        try:
            bucket_dir = self._fs.opendir(bucket_name)
            return bucket_dir.open(file_name, mode="rb").read()
        except (FileExpected, ResourceNotFound) as e:
            logger.error("Resource not found:")
            logger.error(e)
            raise NotFound

    def wipe(self):
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
