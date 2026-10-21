import zipfile as zf
from google.cloud import storage
import functions_framework
import json
import base64
import io
import os

storage_client = storage.Client()
OUTPUT_BUCKET = "unconverted-image-bucket"
CONVERTED_BUCKET = "converted-image-bucket"

@functions_framework.cloud_event
def process_zip(cloud_event):
    #Decode the Pub/Sub message
    message = cloud_event.data["message"]["data"]
    message_decoded = base64.b64decode(message).decode("utf-8")
    message_json = json.loads(message_decoded)
    #Get the file name and bucket name, then get the zip file
    file_name = message_json["name"]
    foldername = file_name.rsplit('.', 1)[0]
    bucket_name = message_json["bucket"]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    target_format = None
    if blob.metadata and "target_format" in blob.metadata: #Retrieve the format the images will be converted to
        target_format = blob.metadata["target_format"]
    zip_file = blob.download_as_bytes()
    #Unzip the file and place the contents in the unconverted image bucket
    count = 0
    with zf.ZipFile(io.BytesIO(zip_file), 'r') as zip:
        for info in zip.infolist():
            if info.is_dir():
                continue
            data = zip.read(info)
            output_blob = storage_client.bucket(OUTPUT_BUCKET).blob(f"{foldername}/{os.path.basename(info.filename)}")
            output_blob.upload_from_string(data)
            output_blob.metadata = {"target_format": target_format}
            output_blob.patch()
            count += 1
    job_blob = storage_client.bucket(CONVERTED_BUCKET).blob(f"jobs/{foldername}.json")
    job = json.loads(job_blob.download_as_bytes())
    job["expected"] = count
    job["status"] = "converting"
    job_blob.upload_from_string(json.dumps(job), content_type="application/json")
