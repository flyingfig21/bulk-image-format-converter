from flask import Flask, render_template, request, redirect
from google.cloud import storage
import json

app = Flask(__name__)

ZIP_BUCKET = "zip-file-bucket" #The name of the bucket the zip files are uploaded to
CONVERTED_BUCKET = "converted-image-bucket" #The name of the bucket the converted images are placed in after conversion

storage_client = storage.Client()

#The starting app route that renders the HTML page where users can select and submit zip files of images to be converted
@app.route('/')
def index():
    return render_template('index.html')

#The app route that handles the upload of zip files to the zip file bucket, the adding of metadata to the zip file to determine which format to convert the images to, and the creation of a JSON file used to keep track of the image conversion process
@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if request.method == 'GET': #If the user is trying to access the page without submitting a file, display the page before performing file processing
        return render_template('convert.html')
    if 'file' not in request.files: #If a user did not select a file before clicking the "Upload File" button, display an error telling the user to upload a file
        return render_template('convert.html', error="File not uploaded")
    file = request.files["file"]
    filename = file.filename
    foldername = filename.rsplit('.', 1)[0] #Isolates the name of the file without the extension
    if filename == "": #If the filename is empty, show an error stating that a file has not been selected
        return render_template('convert.html', error="File not selected")
    if file: #If the user uploaded a valid file, upload the file to the zip file bucket
        convert_type = request.form.get('convert-type')
        output_blob = storage_client.bucket(ZIP_BUCKET).blob(filename)
        output_blob.upload_from_file(file)
        output_blob.metadata = {"target_format": convert_type}
        output_blob.patch()
        job = {
            "expected": None,
            "format": convert_type,
            "status": "unzipping",
            "prefix": f"{foldername}/"
        }
        job_blob = storage_client.bucket(CONVERTED_BUCKET).blob(f"jobs/{foldername}.json")
        job_blob.upload_from_string(json.dumps(job), content_type="application/json")
        return redirect(f"/status/{foldername}")

#The app route that keeps track of the image conversion process, displaying the status page when images have not finished converting, and displaying the converted images to the user once they are finished
@app.route('/status/<job_id>')
def status(job_id):
    bucket = storage_client.bucket(CONVERTED_BUCKET)
    job_blob = bucket.get_blob(f"jobs/{job_id}.json")
    job = json.loads(job_blob.download_as_string())

    completed_prefix = f"jobs/{job_id}/completed/"
    completed_blobs = list(bucket.list_blobs(prefix=completed_prefix))
    completed = len(completed_blobs)
    expected = job.get("expected")

    if expected is not None and completed >= expected: #If all of the images have been converted, retrieve the images and display them to the user.
        prefix = job["prefix"]
        image_blobs = bucket.list_blobs(prefix=prefix)
        urls = [f"https://storage.googleapis.com/{CONVERTED_BUCKET}/{blob.name}" for blob in image_blobs]
        return render_template("convert.html", convert=True, images=urls)

    return render_template("status.html", job=job)

#Run the web app
if __name__ == '__main__':
    app.run(debug=True)
