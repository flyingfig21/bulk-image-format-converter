from flask import Flask, render_template, request, redirect
from google.cloud import storage
import time

app = Flask(__name__)

ZIP_BUCKET = "zip-file-bucket" #The name of the bucket the zip files are uploaded to
CONVERTED_BUCKET = "converted-image-bucket" #The name of the bucket the converted images are placed in after conversion

storage_client = storage.Client()

#The starting app route that renders the HTML page where users can select and submit zip files of images to be converted
@app.route('/')
def index():
    return render_template('index.html')

#The app route that handles the upload of zip files to the zip file bucket and the retrieval of converted images from the converted image bucket
@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if request.method == 'GET': #If the user is trying to access the page without submitting a file, display the page before performing file processing
        return render_template('convert.html')
    if 'file' not in request.files: #If a user did not select a file before clicking the "Upload File" button, display an error telling the user to upload a file
        return render_template('convert.html', error="File not uploaded")
    file = request.files["file"]
    filename = file.filename
    foldername = filename.rsplit('.', 1)[0] #Isolates the name of the file without the extension
    prefix = f"{foldername}/" #The folder name that will be used to identify the image to retrieve for the user
    if filename == "": #If the filename is empty, show an error stating that a file has not been selected
        return render_template('convert.html', error="File not selected")
    if file: #If the user uploaded a valid file, upload the file to the zip file bucket
        output_blob = storage_client.bucket(ZIP_BUCKET).blob(filename)
        output_blob.upload_from_file(file)

    while True: #Polling loop that routinely checks to see if images have been placed in the converted image bucket
        image_blobs = storage_client.bucket(CONVERTED_BUCKET).list_blobs(prefix=prefix, max_results=1)
        time.sleep(0.5)
        if len(list(image_blobs)) > 0: #Once converted images appear in the converted image bucket, break the polling loop
            break

    converted_blobs = storage_client.bucket(CONVERTED_BUCKET).list_blobs(prefix=prefix) #Retrieve the images from the folder containing images only uploaded by the user

    image_urls = []
    for blob in converted_blobs: #For each image from the folder, get the URL of the image and add it to the list of URLs
        url = f"https://storage.googleapis.com/{CONVERTED_BUCKET}/{blob.name}"
        image_urls.append(url)
    return render_template('convert.html', convert=True, images=image_urls) #Render the /convert page indicating the conversion was successful and with the list of URLs

#Run the web app
if __name__ == '__main__':
    app.run(debug=True)
