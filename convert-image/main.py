from PIL import Image
import functions_framework
from google.cloud import storage
import json
import base64
import io

storage_client = storage.Client()
OUTPUT_BUCKET = "converted-image-bucket"

@functions_framework.cloud_event
def convert_image(cloud_event):
    #Decode the Pub/Sub message
    message = cloud_event.data["message"]["data"]
    message_decoded = base64.b64decode(message).decode("utf-8")
    message_json = json.loads(message_decoded)
    #Get the image name and bucket name, then get the image
    file_name = message_json["name"]
    bucket_name = message_json["bucket"]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    image = blob.download_as_bytes()

    #Open the image, convert it to JPEG format, and place it in the converted image bucket
    with Image.open(io.BytesIO(image)) as img:
        img = img.convert("RGB")
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="JPEG")
        converted_image = output_buffer.getvalue()
        output_blob = storage_client.bucket(OUTPUT_BUCKET).blob(file_name)
        output_blob.upload_from_string(converted_image, content_type="image/jpeg")
