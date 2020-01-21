import logging

logger = logging.getLogger("api.bucket")


def get(data):
    logger.info("[BUCKETS] Get received")


def insert(request, response):
    logger.info("[BUCKETS] Insert received {}".format(request))
    response.json({"projectNumber": 1234})
