from flask import Flask, render_template, request, redirect
from google.cloud import storage

app = Flask(__name__)

ZIP_BUCKET = "zip-file-bucket"
storage_client = storage.Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if request.method == 'GET':
        return render_template('convert.html')
    if 'file' not in request.files:
        return render_template('convert.html', error="File not uploaded")
    file = request.files["file"]
    if file.filename == "":
        return render_template('convert.html', error="File not selected")
    if file:
        output_blob = storage_client.bucket(ZIP_BUCKET).blob(file.filename)
        output_blob.upload_from_file(file)
    return render_template('convert.html')

if __name__ == '__main__':
    app.run(debug=True)