import logging
from datetime import datetime

from gcloud_storage_emulator import settings

logger = logging.getLogger("api.bucket")

ALREADY_EXISTING = {
    "error": {
        "errors": [
            {
                "domain": "global",
                "reason": "conflict",
                "message": "You already own this bucket. Please select another name."
            }
        ],
        "code": 409,
        "message": "You already own this bucket. Please select another name."
    }
}

BAD_REQUEST = {
    "error": {
        "errors": [
            {
                "domain": "global",
                "reason": "invalid",
                "message": "Empty bucket name"
            }
        ],
        "code": 400,
        "message": "Empty bucket name"
    }
}


def _make_bucket_resource(bucket_name):
    return {
        "kind": "storage#bucket",
        "id": bucket_name,
        "selfLink": "{}/b/{}".format(settings.API_ENDPOINT, bucket_name),
        "projectNumber": "1234",
        "name": bucket_name,
        "timeCreated": datetime.now().__str__(),
        "updated": datetime.now().__str__(),
        "metageneration": "1",
        "iamConfiguration": {
            "bucketPolicyOnly": {
                "enabled": False
            },
            "uniformBucketLevelAccess": {
                "enabled": False
            }
        },
        "location": "US",
        "locationType": "multi-region",
        "storageClass": "STANDARD",
        "etag": "CAE="
    }


def get(request, response, storage, *args, **kwargs):
    name = request["params"].get("bucket_name")
    if name and storage.buckets.get(name):
        response.json(storage.buckets.get(name))
    else:
        response.status = 404


def ls(request, response, storage, *args, **kwargs):
    logger.info("[BUCKETS] List received")
    response.json({
        "kind": "storage#buckets",
        "items": list(storage.buckets.values()),
    })


def insert(request, response, storage, *args, **kwargs):
    name = request["data"].get("name")
    if name:
        logger.debug("[BUCKETS] Received request to create bucket with name {}".format(name))
        if storage.buckets.get(name):
            response.status = 409
            response.json(ALREADY_EXISTING)
        else:
            bucket = _make_bucket_resource(name)
            storage.buckets[name] = bucket
            response.json(bucket)
    else:
        response.status = 400
        response.json(BAD_REQUEST)
