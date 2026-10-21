from PIL import Image
import functions_framework
from google.cloud import storage
import json
import base64
import io
import os

storage_client = storage.Client()
CONVERTED_BUCKET = "converted-image-bucket"

@functions_framework.cloud_event
def convert_image(cloud_event):
    #Decode the Pub/Sub message
    message = cloud_event.data["message"]["data"]
    message_decoded = base64.b64decode(message).decode("utf-8")
    message_json = json.loads(message_decoded)
    #Get the image name and bucket name, then get the image
    file_name = message_json["name"]
    foldername = file_name.split('/')[0]
    bucket_name = message_json["bucket"]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    target_format = blob.metadata.get("target_format", "JPEG")
    image = blob.download_as_bytes()

    #Open the image, convert it to JPEG format, and place it in the converted image bucket
    with Image.open(io.BytesIO(image)) as img:
        img = img.convert("RGB")
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=target_format)
        converted_image = output_buffer.getvalue()
        base, _ = os.path.splitext(file_name)
        new_file_name = f"{base}.{target_format.lower()}"
        content_type = f"image/{target_format.lower()}"
        output_blob = storage_client.bucket(CONVERTED_BUCKET).blob(new_file_name)
        output_blob.upload_from_string(converted_image, content_type=content_type)
    
    marker_name = f"jobs/{foldername}/completed/{os.path.basename(file_name)}.done"
    marker_blob = storage_client.bucket(CONVERTED_BUCKET).blob(marker_name)
    marker_blob.upload_from_string("", content_type="text/plain")
