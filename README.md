Bulk Image Format Converter

This project is a cloud-based web application designed to take zip files of images uploaded by users, extract the images from the zip files, and convert each image to jpeg format before displaying them to the user where they can download them.

Each of the three main folders in the repository contain the code used for the different parts of the application. The image-converter-app folder contains the Python code, configuration files, and HTML files used in the deployment of the front-facing web application. The unzip-file folder contains the Python code and requirements file used in the deployment of a Google Cloud Run Function for unzipping the files uploaded by users. The convert-image folder contains the Python code and requirements file used in the deployment of a Google Cloud Run Function for converting the images extracted from the zip file to jpeg format.
