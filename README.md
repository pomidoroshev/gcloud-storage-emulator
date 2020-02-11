# Local Emulator for Google Cloud Storage

Google doesn't (yet) ship an emulator for the Cloud Storage API like they do for
Cloud Datastore.

This is a stub emulator so you can run your tests and do local development without
having to connect to the production Storage APIs.

**THIS IS A WORK IN PROGRESS AND ONLY SUPPORTS A LIMITED SUBSET OF API**

## CLI Usage


### Starting the emulator
Start the emulator with:

```bash
$ gcloud-storage-emulator start --port=9090
```

By default, data is stored under `$PWD/.cloudstorage`. You can configure the folder using the env variables `STORAGE_BASE` and `STORAGE_DIR`.

If you wish to run the emulator in a testing environment or if you don't want to persist any data, you can use the `--no-store-on-disk` parameter. For tests, you might want to consider starting up the server from your code (see the [Python APIs](#python-apis))


### Wiping data

You can wipe the data by running

```bash
$ gcloud-storage-emulator wipe
```

## Python APIs

To start a server from your code you can do

```python
from gcloud_storage_emulator.server import create_server

server = create_server("localhost", 9023, in_memory=False)

server.start()
# ........
server.stop()
```

You can wipe the data (e.g. for text execution) by calling `server.wipe()`

This can also be achieved (e.g. during tests) by hitting the `/wipe` endpoint
