import io
import os
import json
import logging
from dateutil import parser, tz

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dominate
from dominate.tags import div, link, script, attr, h3

from azure.cosmosdb.table.tableservice import TableService
import azure.functions as func


connect_str = os.environ["BLOB_STORAGE_CONNECTION_STRING"]
table_service_account_name = os.environ["BLOB_STORAGE_ACCOUNT_NAME"]
table_service_access_key = os.environ["BLOB_STORAGE_ACCESS_KEY"]
table_service_table_name = os.environ["BLOB_STORAGE_TABLE_NAME"]
time_zone = "Asia/Kolkata"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def get_iot_data():
    table_service = TableService(account_name=table_service_account_name, account_key=table_service_access_key)
    table_data_sets = table_service.query_entities(table_service_table_name)

    # Get all the with Date as a Dict
    all_dates = []
    all_temperature = []
    all_humidity = []
    all_air = []
    all_sound = []
    all_lpg = []
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
        all_dates.append(table_data.time)
        all_temperature.append(table_data.temperature)
        all_humidity.append(table_data.humidity)
        all_air.append(table_data.air)
        all_sound.append(table_data.sound)
        all_lpg.append(table_data.lpg)
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

    return { 
        "all_dates": all_dates,
        "all_temperature": all_temperature,
        "all_humidity": all_humidity,
        "all_air": all_air,
        "all_sound": all_sound,
        "all_lpg": all_lpg,
        "data_output": data_output,
        "latest_measures": latest_measures
        }

def create_dash():
    # Get the Data
    iot_data_output_all = get_iot_data()
    iot_all_dates = iot_data_output_all["all_dates"]
    iot_all_temperature = iot_data_output_all["all_temperature"]
    iot_all_humidity = iot_data_output_all["all_humidity"]
    iot_all_air = iot_data_output_all["all_air"]
    iot_all_lpg = iot_data_output_all["all_lpg"]
    iot_latest_measures = iot_data_output_all["latest_measures"]
    iot_latest_measures_date_obj = parser.isoparse(iot_latest_measures[5])
    iot_latest_measures_date_obj = iot_latest_measures_date_obj.astimezone(tz.gettz(time_zone))
    iot_latest_measures_date = iot_latest_measures_date_obj.strftime("%d %b %Y %I:%M %p")
    iot_latest_measures_date = iot_latest_measures_date + " " + time_zone

    # Create the figures to plot
    latest_indicator = make_subplots(rows=1, cols=4,
                                    specs=[[
                                            {'type': 'domain'}, {'type': 'domain'},
                                            {'type': 'domain'}, {'type': 'domain'}
                                            ]],
                                    subplot_titles=["Temperature (ºC)", "Humidity (%)", "Air Pollution (PPM)", "LGP Leakage (PPM)"]
                                    )
    latest_indicator.append_trace(go.Indicator(value = iot_latest_measures[0], mode = "gauge+number", domain = {'row': 0, 'column': 0}), row=1, col=1)
    latest_indicator.append_trace(go.Indicator(value = iot_latest_measures[1], mode = "gauge+number", domain = {'row': 0, 'column': 1}), row=1, col=2)
    latest_indicator.append_trace(go.Indicator(value = iot_latest_measures[2], mode = "gauge+number", domain = {'row': 0, 'column': 2}), row=1, col=3)
    latest_indicator.append_trace(go.Indicator(value = iot_latest_measures[4], mode = "gauge+number", domain = {'row': 0, 'column': 3}), row=1, col=4)
    latest_indicator.update_layout(title_text="Last Measure Time: " + iot_latest_measures_date, title_x=0.5)

    temperature_humidity_line = go.Figure()
    temperature_humidity_line.add_trace(go.Scatter(name="Temperature (ºC)", x=iot_all_dates, y=iot_all_temperature, mode='lines+markers'))
    temperature_humidity_line.add_trace(go.Scatter(name="Humidity (%)", x=iot_all_dates, y=iot_all_humidity, mode='lines+markers'))
    temperature_humidity_line.update_layout(title_text='Temperature (ºC) & Humidity (%)', title_x=0.5)
    temperature_humidity_line.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=14, label="14d", step="day", stepmode="backward"),
                dict(count=21, label="21d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=2, label="2m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=4, label="4m", step="month", stepmode="backward"),
                dict(label="R", step="all")
            ])
        )
    )
    air_lpg_line = go.Figure()
    air_lpg_line.add_trace(go.Scatter(name="Air Pollution (PPM)", x=iot_all_dates, y=iot_all_air, mode='lines+markers'))
    air_lpg_line.add_trace(go.Scatter(name="LGP Leakage (PPM)", x=iot_all_dates, y=iot_all_lpg, mode='lines+markers'))
    air_lpg_line.update_layout(title_text='Air Pollution (PPM) & LGP Leakage (PPM)', title_x=0.5)
    air_lpg_line.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=14, label="14d", step="day", stepmode="backward"),
                dict(count=21, label="21d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=2, label="2m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=4, label="4m", step="month", stepmode="backward"),
                dict(label="R", step="all")
            ])
        )
    )

    doc = dominate.document(title='Home IOT Dashboard')
    with doc.head:
        link(rel='stylesheet', href='https://codepen.io/chriddyp/pen/bWLwgP.css')
        script(type='text/javascript', src="https://cdn.plot.ly/plotly-latest.min.js")
        link(rel="icon", type="image/x-icon", href="data:image/x-icon;base64,AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbAAACnAUBJ98BAASnAAAAIwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAABxAAAC5DIEvf9FBP3/NwTP/wIACukAAAByAAAACgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABACAAm/IQKH/w4BSv8LAUP/HwKF/xMCWf8MAUX/IwKN/wMAF9EAAAAhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGALAOt/0wF//8eAn3/HAJ6/zoE2P8kA5T/HgJ//0sE//81BMj/AQAEpwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0j8E6v81BMv/BQEn/0ME9v9CBPX/RwT//xMCWv82BM3/RwT//wMBFN4AAAAAAAAAAAAAAAAAAAAAAAAARw4CSf8OAkz/AwEX/wUBJP8rA6b/QgT0/zMDxP8FAST/BQEp/x4CgP8LAUT9AAAAQwAAAAAAAAAAAAAAAAAAAaA9BOL/CgE//ykDo/9CBPX/JgOa/wUBKf8bAnP/PgTn/ywDrf8IATf/OwTc/wAAAZ0AAAAAAAAAAAAAAAAAAAGCMQO8/x0Cev8+BOT/QgTz/0ME+f8JATr/PATe/0IE9v9ABO7/IgOL/zMEw/8AAAGHAAAAAAAAAAAAAAAAAAAAFQMAFdMFASn/IwKO/0YE//88BOD/BAEd/zYEzf9HBP//KwOn/woBO/8EAR/aAAAAGwAAAAAAAAAAAAAAAAAAAAAAAABrJgOb/xsCdv8QAk//GgJw/xsCdf8hA4b/FgJl/yECh/8lA5j/AAAAZwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwcANN83AM//DgBH/y8Ct/9LBP//OAPU/xQAWv81AMr/BgAt3gAAABYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAQC2AFEy/wRmTP8EBh7/DwBP/wQCHf8DWkX/AF81/wAEAMsAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB/AHA2/wDIWP8AulD/AFId/wAGAP8APAv/AK9M/wDJWf8AjEL/AQMCrQAAAAAAAAAAAAAAAAAAAAAAAAAKAR8K6QDCXP8Aq1H/AJBF/wC6V/8ANRf/ALBQ/wCVRP8Ao0z/AMle/wBAHf8AAAAkAAAAAAAAAAAAAAAAAAAAGAEkDv8AoEv/AKlQ/wCvUf8AdDb/AAIBvwBcKf8ArFD/AKtR/wClT/8AQR7/AAAAPAAAAAAAAAAAAAAAAAAAAAIAAABSAQICngISBtMBBwS6AAAAbwAAAAQAAABXAQQDsQITB9MBBAOrAAAAZAAAAAkAAAAA/j8AAPwfAADwBwAA4AMAAOADAADgAwAAwAEAAMABAADgAwAA8AcAAPAHAADwBwAA8AMAAOADAADgAwAA8ccAAA==")

    with doc.body:
        with div():
            attr(cls='body', style="text-align:center;")
            h3('Azure IoT based Home Sensors Dashboard')

        doc.add_raw_string(latest_indicator.to_html(full_html=False))
        doc.add_raw_string(temperature_humidity_line.to_html(full_html=False))
        doc.add_raw_string(air_lpg_line.to_html(full_html=False))
        doc.add_raw_string('<p style="text-align:center;bottom: 0;">Source Code - https://github.com/prabdeb/azure-iot-sample-home-alerts</p>')

    return doc

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    doc = create_dash()
    return func.HttpResponse(doc.render(), mimetype='text/html')