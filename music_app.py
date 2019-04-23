#!/usr/bin/env python3

from flask import Flask, render_template, flash, redirect, request, url_for
import os
from azure.storage.blob import BlockBlobService, PublicAccess

ALLOWED_EXTENSIONS= set(['mp3'])

AZURE_STORAGE_KEY = os.environ['AZURE_STORAGE_KEY']
AZURE_ACCOUNT = 'blueplayerstorage'
DEFAULT_CONTAINER = "blue-player"
blob_service = BlockBlobService(account_name=AZURE_ACCOUNT,
                                      account_key=AZURE_STORAGE_KEY)

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
container = DEFAULT_CONTAINER

@app.route("/")
def hello():
    return redirect(url_for("home"))


@app.route("/home")
def home():
    if not blob_service.exists(container):
        blob_service.create_container(container, public_access='container')
    music_blobs = blob_service.list_blobs(container)
    music = []
    for blob in music_blobs:
        music.append(blob.name)

    return render_template("index.html", music=music)

def _allowed_files(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            flash("no file selected!", 'danger')
            return redirect(request.url)
        if file:
            if _allowed_files(file.filename):
                flash(file.filename + " uploaded", 'success')
                blob_service.create_blob_from_stream(container, file.filename,
                                                     file.stream)
            else:
                flash(file.filename + " is not a valid music file")
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
