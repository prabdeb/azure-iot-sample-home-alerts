import io
import os
import json
from dateutil import parser, tz
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from flask import Flask, flash, redirect, render_template, request, session, abort

connect_str = os.environ["CUSTOMCONNSTR_BLOB_STORAGE_CONNECTION_STRING"]
time_zone = "Asia/Kolkata"

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

def get_iot_data():
    # Create the BlobServiceClient object which will be used to create a container client
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # List the blobs in the container
    container_client = blob_service_client.get_container_client("raw")
    blob_list = container_client.list_blobs()

    # Get the blob contents
    all_blobs_content = []
    for blob in blob_list:
        blob_client = blob_service_client.get_blob_client("raw", blob.name)
        file_content = blob_client.download_blob().readall()
        file_content_as_a_list = (file_content.decode("utf-8")).splitlines( )
        all_blobs_content = all_blobs_content + file_content_as_a_list

    # Get all the with Date as a Dict
    data_output = []
    latest_measures = []
    for data in all_blobs_content:
        data_json_obj = json.loads(data)
        data_output.append([
            int(data_json_obj["temperature"]),
            int(data_json_obj["humidity"]),
            int(data_json_obj["air"]),
            int(data_json_obj["sound"]),
            int(data_json_obj["lpg"]),
            data_json_obj["time"]
        ])
        if len(latest_measures) == 0:
            latest_measures = [
                int(data_json_obj["temperature"]),
                int(data_json_obj["humidity"]),
                int(data_json_obj["air"]),
                int(data_json_obj["sound"]),
                int(data_json_obj["lpg"]),
                data_json_obj["time"]
            ]
        else:
            datetime_new = parser.isoparse(data_json_obj["time"])
            datetime_stored = parser.isoparse(latest_measures[5])
            if datetime_new > datetime_stored:
                latest_measures = [
                    int(data_json_obj["temperature"]),
                    int(data_json_obj["humidity"]),
                    int(data_json_obj["air"]),
                    int(data_json_obj["sound"]),
                    int(data_json_obj["lpg"]),
                    data_json_obj["time"]
                ]

    return { "data_output": data_output, "latest_measures": latest_measures }

@app.route("/")
def index():
    iot_data_output_all = get_iot_data()
    iot_data_output = iot_data_output_all["data_output"]
    iot_latest_measures = iot_data_output_all["latest_measures"]
    iot_latest_measures_date_obj = parser.isoparse(iot_latest_measures[5])
    iot_latest_measures_date_obj = iot_latest_measures_date_obj.astimezone(tz.gettz(time_zone))
    iot_latest_measures_date = iot_latest_measures_date_obj.strftime("%d %b %Y %I:%M %p")
    iot_latest_measures_date = iot_latest_measures_date + " " + time_zone

    return render_template('index.html',
                           len = len(iot_data_output),
                           iot_data_output = iot_data_output,
                           iot_latest_measures = iot_latest_measures,
                           iot_latest_measures_date = iot_latest_measures_date
                          )

if __name__ == "__main__":
    app.run()