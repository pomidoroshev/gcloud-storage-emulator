import time
import math
from http import HTTPStatus

def _make_object_resource(bucket_name, object_name, content_type, content_length):
    time_id = math.floor(time.time())

    return {
        "kind": "storage#object",
        "id": "{}/{}/{}".format(bucket_name, object_name, time_id),
        "selfLink": "/storage/v1/b/{}/o/{}".format(bucket_name, object_name),
        "name": object_name,
        "bucket": bucket_name,
        "generation": str(time_id),
        "metageneration": "1",
        "contentType": content_type,
        "timeCreated": "2020-01-24T11:14:43.743Z",
        "updated": "2020-01-24T11:14:43.743Z",
        "storageClass": "STANDARD",
        "timeStorageClassUpdated": "2020-01-24T11:14:43.743Z",
        "size": content_length,
        "md5Hash": "NOT_IMPLEMENTED",
        "mediaLink": "/download/storage/v1/b/{}/o/{}?generation={}&alt=media".format(
            bucket_name, object_name, time_id
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
        request.params["bucket_name"],
        request.data["meta"]["name"],
        request.data["content-type"],
        str(len(request.data["content"])),
    )
    storage.create_file(request.params["bucket_name"], request.data["meta"]["name"], request.data["content"], request.data["content-type"], obj)
    print(obj)
    print(request.base_url)
    # bucket_name = request.params["bucket_name"]
