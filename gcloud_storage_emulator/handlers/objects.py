def insert(request, response, storage, *args, **kwargs):
    uploadType = request["query"].get("uploadType")

    if not uploadType or len(uploadType) == 0:
        response.status = 400
        return

    uploadType = uploadType[0]

    if uploadType == "resumable":
        raise Exception("Not implemented")

    storage.create_file(request["params"]["bucket_name"], request["data"]["meta"]["name"], request["data"]["content"])
    print(request)
    # bucket_name = request["params"]["bucket_name"]
