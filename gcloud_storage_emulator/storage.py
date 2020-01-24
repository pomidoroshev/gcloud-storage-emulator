import fs


class Storage(object):
    buckets = {}

    def __init__(self):
        pwd = fs.open_fs('osfs://~/dev/gcloud-cloudstore-emulator/')
        try:
            self._fs = pwd.makedir('.cloudstorage')
        except fs.errors.DirectoryExists:
            self._fs = pwd.opendir('.cloudstorage')

        self.buckets = {}
        self.objects = {}

    def create_file(self, bucket_name, file_name, content, content_type, object):
        try:
            bucket_dir = self._fs.makedir(bucket_name)
        except fs.errors.DirectoryExists:
            bucket_dir = self._fs.opendir(bucket_name)

        with bucket_dir.open(file_name, mode="w") as file:
            file.write(content)
            bucket_objects = self.objects.get(bucket_name, {})
            # bucket_objects[file_name] = ....
            self.objects[bucket_name] = bucket_objects
