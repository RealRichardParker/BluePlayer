#!/usr/bin/env python3

from flask import Flask, render_template, flash, redirect, request, url_for
import os
from azure.storage.blob import BlockBlobService, PublicAccess, ContainerPermissions
import adal
from msrestazure.azure_active_directory import AdalAuthentication
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
from azure.mgmt.media import AzureMediaServices
from azure.mgmt.media.models import (MediaService, Asset, TransformOutput,
                                     BuiltInStandardEncoderPreset,
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
AZURE_STORAGE_KEY = os.environ['AZURE_STORAGE_KEY']
AZURE_ACCOUNT = 'blueplayerstorage'
DEFAULT_CONTAINER = "blue-player"
TRANSFORM_NAME = "blue-player-transform"

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


app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
container = DEFAULT_CONTAINER

@app.route("/")
def hello():
    transforms=[
        TransformOutput(
            preset=BuiltInStandardEncoderPreset(
                preset_name='AdaptiveStreaming'
            )
        )
    ]
    client.transforms.create_or_update(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME,
        TRANSFORM_NAME,
        transforms
    )
    return redirect(url_for("home"))

def _get_music(asset_list, base_url):
    music = []
    for asset in asset_list:
        print(asset.name)
        if(asset.name.startswith('out__')):
            basename = asset.name[5:]
            url = asset.description

            #no streaming locator
            if not url:
                print("No streaming locator for " + asset.name)
                response = client.jobs.get(
                    RESOURCE_GROUP_NAME,
                    ACCOUNT_NAME,
                    TRANSFORM_NAME,
                    "job__" + basename
                )
                #No streaming locator, but finished encoding, so must create
                if response.state == 'Finished':
                    print("Job is finished, creating locator for " + asset.name)

                    #Check thaat locator doesnt already exist
                    locator = client.streaming_locators.get(
                        RESOURCE_GROUP_NAME,
                        ACCOUNT_NAME,
                        "loc__" + basename
                    )
                    if not locator:
                        client.streaming_locators.create(
                            RESOURCE_GROUP_NAME,
                            ACCOUNT_NAME,
                            "loc__" + basename,
                            StreamingLocator(
                                asset_name=asset.name,
                                streaming_policy_name=
                                    'Predefined_ClearStreamingOnly'
                            )
                        )

                    #Generate streaming path and add to asset
                    paths = client.streaming_locators.list_paths(
                        RESOURCE_GROUP_NAME,
                        ACCOUNT_NAME,
                        "loc__" + basename
                    )
                    path = ""
                    for item in paths.streaming_paths:
                        path = item.paths[0]
                    url = base_url + path
                    update = Asset(
                        alternate_id=asset.alternate_id,
                        description=url)
                    print("adding url: " + url + "to " + asset.name)
                    client.assets.create_or_update(
                        RESOURCE_GROUP_NAME,
                        ACCOUNT_NAME,
                        asset.name,
                        update
                    )
                    music.append(basename)
                    print(url)
            # Streaming locator already exists
            else:
                print(url)
                music.append(basename)
    return music

@app.route("/home")
def home():
    #Get streaming endpoint and start it if it is stopped
    response = client.streaming_endpoints.get(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME,
        'default'
    )
    if response.resource_state == 'Stopped':
        client.streaming_endpoints.start(
            RESOURCE_GROUP_NAME,
            ACCOUNT_NAME,
            'default'
        )
    base_url = response.host_name

    response = client.assets.list(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME
    )

    #Get list of music uploaded and avaliable to stream
    music = _get_music(response, base_url)

    return render_template("index.html", music=music)

def _allowed_files(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def  _upload_and_encode(file):
    # clean up inputs
    basename = file.filename.replace('.', '-')
    basename = basename.replace(' ', '-')
    in_asset = "in__" + basename
    print(in_asset)

    # Create new input asset
    client.assets.create_or_update(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME,in_asset,
        Asset()
    )

    #Get asset container and upload file to it
    response = client.assets.get(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME,
        in_asset
    )
    print("got a response, know what kind of container??")
    print(response.container)

    blob_service.create_blob_from_stream(
        response.container,
        basename,
        stream=file.stream
    )

    #Create output asset and add streaming locator name to it as metadata
    out_asset = "out__" + basename
    locator_name = "loc__" + basename
    client.assets.create_or_update(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME,
        out_asset,
        Asset(alternate_id=locator_name)
    )

    #Check if job exists, delete it if it does
    job_name = "job__" + basename
    response = client.jobs.get(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME,
        TRANSFORM_NAME,
        job_name
    )
    if response:
        client.jobs.delete(
            RESOURCE_GROUP_NAME,
            ACCOUNT_NAME,
            TRANSFORM_NAME,
            job_name
        )

    #Create new job with corret inputs and outputs
    inputs = JobInputAsset(asset_name=in_asset)
    outputs = [JobOutputAsset(asset_name=out_asset)]
    new_job = Job(input=inputs, outputs=outputs)
    print("Creating new job")
    client.jobs.create(
        RESOURCE_GROUP_NAME,
        ACCOUNT_NAME,
        TRANSFORM_NAME,
        job_name, new_job
    )

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    #Uploading file
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            flash("no file selected!", 'danger')
            return redirect(request.url)
        if file:
            if _allowed_files(file.filename):
                _upload_and_encode(file)

                flash(file.filename + " uploaded", 'success')

            else:
                flash(file.filename + " is not a valid music file")
    #Going to upload page
    if request.method == 'GET':
        return render_template("upload.html")
    return redirect(url_for("upload"))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
