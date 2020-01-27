import os

API_ENDPOINT = "/storage/v1"
UPLOAD_API_ENDPOINT = "/upload/storage/v1"
BATCH_API_ENDPOINT = "/batch/storage/v1"
DOWNLOAD_API_ENDPOINT = "/download/storage/v1"

STORAGE_BASE = "osfs://{}/".format(os.getcwd())
STORAGE_DIR = ".cloudstorage"
