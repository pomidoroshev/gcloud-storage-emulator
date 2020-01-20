# Local Emulator for Google Cloud Storage

Google doesn't (yet) ship an emulator for the Cloud Storage API like they do for
Cloud Datastore.

This is a stub emulator so you can run your tests and do local development without
having to connect to the production Storage API.

**THIS IS A WORK IN PROGRESS NOT ALL API CALLS ARE COMPLETE**

## Usage

Start the emulator with:

```
gcloud-storage-emulator start --port=9090
```
