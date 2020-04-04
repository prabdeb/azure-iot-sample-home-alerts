import io
import os
import json
import logging
from dateutil import parser, tz
from azure.cosmosdb.table.tableservice import TableService
from flask import Flask, flash, redirect, render_template, request, session, abort
import azure.functions as func


connect_str = os.environ["BLOB_STORAGE_CONNECTION_STRING"]
table_service_account_name = os.environ["BLOB_STORAGE_ACCOUNT_NAME"]
table_service_access_key = os.environ["BLOB_STORAGE_ACCESS_KEY"]
table_service_table_name = os.environ["BLOB_STORAGE_TABLE_NAME"]
time_zone = "Asia/Kolkata"

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

def get_iot_data():
    table_service = TableService(account_name=table_service_account_name, account_key=table_service_access_key)
    table_data_sets = table_service.query_entities(table_service_table_name)

    # Get all the with Date as a Dict
    data_output = []
    latest_measures = []
    for table_data in table_data_sets:
        data_output.append([
            int(table_data.temperature),
            int(table_data.humidity),
            int(table_data.air),
            int(table_data.sound),
            int(table_data.lpg),
            table_data.time
        ])
        if len(latest_measures) == 0:
            latest_measures = [
                int(table_data.temperature),
                int(table_data.humidity),
                int(table_data.air),
                int(table_data.sound),
                int(table_data.lpg),
                table_data.time
            ]
        else:
            datetime_new = parser.isoparse(table_data.time)
            datetime_stored = parser.isoparse(latest_measures[5])
            if datetime_new > datetime_stored:
                latest_measures = [
                    int(table_data.temperature),
                    int(table_data.humidity),
                    int(table_data.air),
                    int(table_data.sound),
                    int(table_data.lpg),
                    table_data.time
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

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    with app.test_client() as c:
        doAction = {
            "GET": c.get("/").data,
        }
        resp = doAction.get(req.method).decode()
        return func.HttpResponse(resp, mimetype='text/html')
