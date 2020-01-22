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

ERROR = {
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


def get(data):
    logger.info("[BUCKETS] Get received")


def insert(request, response):
    name = request["data"].get("name", None)
    if name:
        logger.debug("[BUCKETS] Received request to create bucket with name {}".format(name))
        bucket = _make_bucket_resource(name)
        response.json(bucket)
