# Local Emulator for Google Cloud Storage

Google doesn't (yet) ship an emulator for the Cloud Storage API like they do for
Cloud Datastore.

This is a stub emulator so you can run your tests and do local development without
having to connect to the production Storage APIs.

**THIS IS A WORK IN PROGRESS AND ONLY SUPPORTS A LIMITED SUBSET OF THE API**


---

## Looking for Commercial Support?

Potato offers Commercial Support for all its Open Source projects and we can tailor a support package to your needs.

If you're interested in commercial support, training, or consultancy then go ahead and contact us at [opensource@potatolondon.com](mailto:opensource@potatolondon.com)

---

## Installation

`pip install gcloud-storage-emulator`



## CLI Usage


### Starting the emulator
Start the emulator with:

```bash
$ gcloud-storage-emulator start --port=9090
```

By default, data is stored under `$PWD/.cloudstorage`. You can configure the folder using the env variables `STORAGE_BASE` and `STORAGE_DIR`.

If you wish to run the emulator in a testing environment or if you don't want to persist any data, you can use the `--no-store-on-disk` parameter. For tests, you might want to consider starting up the server from your code (see the [Python APIs](#python-apis))

If you're using the Google client library (e.g. `google-cloud-storage` for Python) then you can set the `STORAGE_EMULATOR_HOST` environment variable to tell the library to connect to your emulator endpoint rather than the standard `https://storage.googleapis.com`, e.g.:

```bash
$ export STORAGE_EMULATOR_HOST=http://localhost:9090
```


### Wiping data

You can wipe the data by running

```bash
$ gcloud-storage-emulator wipe
```

You can pass `--keep-buckets` to wipe the data while keeping the buckets.

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


## Running Tests

### With Tox

If you have Tox installed then you can run tests with:

```bash
tox -e py37 -- {extra_pytest_args}
```

### With Docker

If you don't have Tox installed on your system but you do have Docker, then you can run the tests using the [themattrix/tox](https://github.com/themattrix/docker-tox) image:

```bash
docker run -v /ABSOLUTE/PATH/TO/THIS/REPO/ON/YOUR/MACHINE:/app themattrix/tox tox -e py37 [optional additional args for tox...]
```

### With unittest

* Create and activate a virtualenv (optional but recommended)
* `cd` into the repository directory
* `pip install -e`
* `python -m unittest gcloud_storage_emulator.tests`
