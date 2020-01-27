import math
import time
from datetime import datetime
from http import HTTPStatus

from gcloud_storage_emulator.exceptions import NotFound


def _make_object_resource(base_url, bucket_name, object_name, content_type, content_length):
    time_id = math.floor(time.time())
    now = str(datetime.now())

    return {
        "kind": "storage#object",
        "id": "{}/{}/{}".format(bucket_name, object_name, time_id),
        "selfLink": "/storage/v1/b/{}/o/{}".format(bucket_name, object_name),
        "name": object_name,
        "bucket": bucket_name,
        "generation": str(time_id),
        "metageneration": "1",
        "contentType": content_type,
        "timeCreated": now,
        "updated": now,
        "storageClass": "STANDARD",
        "timeStorageClassUpdated": now,
        "size": content_length,
        "md5Hash": "NOT_IMPLEMENTED",
        "mediaLink": "{}/download/storage/v1/b/{}/o/{}?generation={}&alt=media".format(
            base_url,
            bucket_name,
            object_name,
            time_id,
        ),
        "crc32c": "lj+ong==",
        "etag": "CO6Q4+qNnOcCEAE="
    }


def insert(request, response, storage, *args, **kwargs):
    uploadType = request.query.get("uploadType")

    if not uploadType or len(uploadType) == 0:
        response.status = HTTPStatus.BAD_REQUEST
        return

    uploadType = uploadType[0]

    if uploadType == "resumable":
        raise Exception("Not implemented")

    obj = _make_object_resource(
        request.base_url,
        request.params["bucket_name"],
        request.data["meta"]["name"],
        request.data["content-type"],
        str(len(request.data["content"])),
    )

    storage.create_file(
        request.params["bucket_name"],
        request.data["meta"]["name"],
        request.data["content"],
        request.data["content-type"],
        obj,
    )

    response.json(obj)


def get(request, response, storage, *args, **kwargs):
    try:
        obj = storage.get_file_obj(request.params["bucket_name"], request.params["object_id"])
        response.json(obj)
    except NotFound:
        response.status = HTTPStatus.NOT_FOUND


def download(request, response, storage, *args, **kwargs):
    try:
        file = storage.get_file(request.params["bucket_name"], request.params["object_id"])
        obj = storage.get_file_obj(request.params["bucket_name"], request.params["object_id"])
        response.write_file(file, content_type=obj.get("contentType"))
    except NotFound:
        response.status = HTTPStatus.NOT_FOUND
