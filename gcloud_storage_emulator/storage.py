import fs
from gcloud_storage_emulator.settings import STORAGE_BASE, STORAGE_DIR
from gcloud_storage_emulator.exceptions import NotFound


class Storage(object):
    buckets = {}

    def __init__(self):
        self._pwd = fs.open_fs(STORAGE_BASE)
        try:
            self._fs = self._pwd.makedir(STORAGE_DIR)
        except fs.errors.DirectoryExists:
            self._fs = self._pwd.opendir(STORAGE_DIR)

        self.buckets = {}
        self.objects = {}

    def create_file(self, bucket_name, file_name, content, content_type, file_obj):
        try:
            bucket_dir = self._fs.makedir(bucket_name)
        except fs.errors.DirectoryExists:
            bucket_dir = self._fs.opendir(bucket_name)

        with bucket_dir.open(file_name, mode="w") as file:
            file.write(content)
            bucket_objects = self.objects.get(bucket_name, {})
            bucket_objects[file_name] = file_obj
            self.objects[bucket_name] = bucket_objects

    def get_file_obj(self, bucket_name, file_name):
        try:
            return self.objects[bucket_name][file_name]
        except KeyError:
            raise NotFound

    def reset(self):
        self.buckets = {}
        self.objects = {}
        for path in self._fs.listdir('.'):
            self._fs.removetree(path)
