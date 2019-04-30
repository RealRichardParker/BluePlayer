#!/usr/bin/env python3

from flask import Flask, render_template, flash, redirect, request, url_for
import os
from azure.storage.blob import BlockBlobService, PublicAccess
import adal
from msrestazure.azure_active_directory import AdalAuthentication
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (MediaService, Asset, StandardEncoderPreset,
                                     TransformOutput, AacAudio, Mp4Format,
                                     JobInputAsset, Job, JobOutputAsset,
                                     StreamingLocator)
from azure.mgmt.media.operations import AssetsOperations

RESOURCE = 'https://management.core.windows.net/'
TENANT_ID = os.environ['TENANT_ID']
CLIENT = os.environ['CLIENT']
KEY = os.environ['KEY']
SUBSCRIPTION_ID = os.environ['SUBSCRIPTION_ID']
ACCOUNT_NAME = 'blueplayermedia'
RESOURCE_GROUP_NAME = 'BluePlayer'

LOGIN_ENDPOINT = AZURE_PUBLIC_CLOUD.endpoints.active_directory
RESOURCE = AZURE_PUBLIC_CLOUD.endpoints.active_directory_resource_id

context = adal.AuthenticationContext(LOGIN_ENDPOINT + '/' + TENANT_ID)
credentials = AdalAuthentication(
    context.acquire_token_with_client_credentials,
    RESOURCE,
    CLIENT,
    KEY
)

# The AMS Client
client = AzureMediaServices(credentials, SUBSCRIPTION_ID)
# Blob service client
blob_service = BlockBlobService(account_name=AZURE_ACCOUNT,
                                account_key=AZURE_STORAGE_KEY)

ALLOWED_EXTENSIONS= set(['mp3'])

AZURE_STORAGE_KEY = os.environ['AZURE_STORAGE_KEY']
AZURE_ACCOUNT = 'blueplayerstorage'
DEFAULT_CONTAINER = "blue-player"
INPUT_ASSET = "blue-player-input-asset"
INPUT_CONTAINER = "asset-input-container"
OUTPUT_ASSET = "blue-player-output-asset"
OUTPUT_ASSET = "asset-output-container"
TRANSFORM_NAME = "blue-player-transform"
JOB_NAME = "blue-player-job"
STREAMING_LOCATOR = "blue-player-streaming-locator"

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

    if not blob_service.exists(INPUT_CONTAINER):
        blob_service.create_container(container, )

    if not client.assets.get(RESOURCE_GROUP_NAME, ACCOUNT_NAME, INPUT_ASSET):
        print("Creating Input Asset")
        asset_in = Asset(storage_account_name=AZURE_ACCOUNT)
        client.assets.create_or_update(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                       INPUT_ASSET, asset_in)

    if not client.assets.get(RESOURCE_GROUP_NAME, ACCOUNT_NAME, OUTPUT_ASSET):
        print("Creating Output Asset")
        asset_out = Asset(storage_account_name=AZURE_ACCOUNT)
        client.assets.create_or_update(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                       OUTPUT_ASSET, asset_out)

    if not client.streaming_locators.get(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                         STREAMING_LOCATOR):
        print("Creating StreamingLocator")
        locator = StreamingLocator(asset_name=OUTPUT_ASSET,
                                   streaming_policy_name=
                                   "Predefined_ClearStreamingOnly")
        client.streaming_locators.create(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                        STREAMING_LOCATOR, locator)
    paths = client.streaming_locators.list_paths(RESOURCE_GROUP_NAME, ACCOUNT_NAME, STREAMING_LOCATOR).streaming_paths
    for path in paths:
        print(path.paths)

    music_blobs = blob_service.list_blobs(container)
    music = []
    for blob in music_blobs:
        music.append(blob.name)
    #use standardencoderpreset, need codecs: Audio? and formats: Mp4Format?
    codecs = [AacAudio()]
    formats = [Mp4Format(filename_pattern="{Basename}_AAC_{AudioBitrate}.mp4")]
    transforms=[(TransformOutput(preset=
                                 StandardEncoderPreset(codecs=codecs,
                                                       formats=formats)))]
    if not client.transforms.get(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                 TRANSFORM_NAME):
        client.transforms.create_or_update(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                           TRANSFORM_NAME,transforms)

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
                response = client.assets.get(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                             INPUT_ASSET)
                blob_service.create_blob_from_stream(response.container,
                                                     file.filename,
                                                     stream=file.stream)
                inputs = JobInputAsset(asset_name=INPUT_ASSET)
                outputs = [JobOutputAsset(asset_name=OUTPUT_ASSET)]
                new_job = Job(input=inputs, outputs=outputs)
                client.jobs.create(RESOURCE_GROUP_NAME, ACCOUNT_NAME,
                                   TRANSFORM_NAME, JOB_NAME, new_job)

            else:
                flash(file.filename + " is not a valid music file")
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
