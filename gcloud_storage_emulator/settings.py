API_ENDPOINT = "/storage/v1"
UPLOAD_API_ENDPOINT = "/upload/storage/v1"
BATCH_API_ENDPOINT = "/batch/storage/v1"

import os

STORAGE_BASE = "osfs://{}/".format(os.getcwd())
import logging
logging.error(os.getcwd())
STORAGE_DIR = ".cloudstorage"
