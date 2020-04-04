import os
import threading
import time
import logging
import json
import statistics
from datetime import datetime, timezone

import azure.functions as func
from azure.eventhub import EventHubConsumerClient
from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore
from azure.cosmosdb.table.tableservice import TableService

connection_str = os.environ['EH_CONNECTION_STRING']
consumer_group = '$default'
eventhub_name = os.environ['EH_NAME']

storage_connection_str = os.environ['BLOB_STORAGE_CONNECTION_STRING']
container_name = os.environ["BLOB_STORAGE_CONTAINER_HISTORICAL_EH_CHECKPOINT"]
table_service_account_name = os.environ["BLOB_STORAGE_ACCOUNT_NAME"]
table_service_access_key = os.environ["BLOB_STORAGE_ACCESS_KEY"]
table_service_table_name = os.environ["BLOB_STORAGE_TABLE_NAME"]

def receive_events(receive_duration=15):
    '''
    Receive events from EH
    '''
    received_events = []

    checkpoint_store = BlobCheckpointStore.from_connection_string(storage_connection_str, container_name)
    consumer_client = EventHubConsumerClient.from_connection_string(
        connection_str,
        consumer_group,
        eventhub_name=eventhub_name,
        checkpoint_store=checkpoint_store,
    )

    def on_event(partition_context, event):
        received_events.append({"message": event.body_as_str(encoding='UTF-8'),
                                "properties": event.properties})
        partition_context.update_checkpoint(event)

    print('[receive_events] - Consumer will keep receiving for %d seconds, start time is %f.', receive_duration, time.time())
    try:
        thread = threading.Thread(
            target=consumer_client.receive,
            kwargs={
                "on_event": on_event,
                "starting_position": "-1",
            }
        )
        thread.start()
        time.sleep(receive_duration)
        consumer_client.close()
        thread.join()
    except Exception as ex:
        print('[receive_events] - error while receiving events - %s', ex)
    finally:
        print('[receive_events] - Consumer has stopped receiving, end time is %f.', time.time())
        print('[receive_events] - Consumer has stopped receiving, end time is %f and total events are - %d', time.time(), len(received_events))

    return received_events

def main(historical: func.TimerRequest) -> None:
    received_events = receive_events()
    pasred_events_data = {
        "temperature": [],
        "humidity": [],
        "air": [],
        "sound": [],
        "lpg": []
    }
    for event in received_events:
        event_message = json.loads(event["message"])
        pasred_events_data["temperature"].append(event_message["temperature"])
        pasred_events_data["humidity"].append(event_message["humidity"])
        pasred_events_data["air"].append(event_message["air"])
        pasred_events_data["sound"].append(event_message["sound"])
        pasred_events_data["lpg"].append(event_message["lpg"])
    averaged_pasred_events_data = {
        'PartitionKey': datetime.now(timezone.utc).strftime("%m"),
        'RowKey': datetime.now(timezone.utc).strftime("%s"),
        "temperature": statistics.mean(pasred_events_data["temperature"]),
        "humidity": statistics.mean(pasred_events_data["humidity"]),
        "air": statistics.mean(pasred_events_data["air"]),
        "sound": statistics.mean(pasred_events_data["sound"]),
        "lpg": statistics.mean(pasred_events_data["lpg"]),
        "time": datetime.now(timezone.utc).isoformat()
    }
    print(averaged_pasred_events_data)

    table_service = TableService(account_name=table_service_account_name, account_key=table_service_access_key)
    table_service.insert_entity(table_service_table_name, averaged_pasred_events_data)
