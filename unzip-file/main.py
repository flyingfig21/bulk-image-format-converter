import zipfile as zf
from google.cloud import storage
import functions_framework
import json
import base64
import io

storage_client = storage.Client()
OUTPUT_BUCKET = "unconverted-image-bucket"

@functions_framework.cloud_event
def process_zip(cloud_event):
    #Decode the Pub/Sub message
    message = cloud_event.data["message"]["data"]
    message_decoded = base64.b64decode(message).decode("utf-8")
    message_json = json.loads(message_decoded)
    #Get the file name and bucket name, then get the zip file
    file_name = message_json["name"]
    bucket_name = message_json["bucket"]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    zip_file = blob.download_as_bytes()
    #Unzip the file and place the contents in the unconverted image bucket
    with zf.ZipFile(io.BytesIO(zip_file), 'r') as zip:
        for info in zip.infolist():
            if info.is_dir():
                continue
            data = zip.read(info)
            output_blob = storage_client.bucket(OUTPUT_BUCKET).blob(info.filename)
            output_blob.upload_from_string(data)
