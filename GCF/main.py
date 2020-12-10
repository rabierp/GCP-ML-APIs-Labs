import flask
import json
import base64
import os
from google.cloud import pubsub_v1
from google.cloud import storage
from google.cloud import vision
from google.cloud import videointelligence
from google.cloud import bigquery

publisher = pubsub_v1.PublisherClient()
storage_client = storage.Client()
vision_client = vision.ImageAnnotatorClient()
video_client = videointelligence.VideoIntelligenceServiceClient()

project_id = os.environ["GCP_PROJECT"]

with open("./config.json", "r") as configfile:
    config = json.load(configfile)

def validate_message(message, param):
    var = message.get(param)
    if not var:
        raise ValueError(
            "{} is not provided. Make sure you have \
                          property {} in the request".format(
                param, param
            )
        )
    return var

def GCStoPubsub(event, context):
    import base64

    print("""This Function was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))

    message = json.loads(base64.b64decode(event['data']).decode('utf-8'))

    bucket_name = message['bucket']
    file_name = message['name']
    content_type = message['contentType']

    print("File:{} of type {} uploaded in Bucket: {}".format(file_name, content_type, bucket_name))

    if "image" not in content_type and "video" not in content_type:
        print('Unsupported ContentType provided. Make sure you upload an image or video which includes a "contentType" property of image or video in your request')
        return 'Unsupported file type.'
    else:
        src_bucket = storage_client.bucket(bucket_name)
        src_blob = src_bucket.blob(file_name)
        dest_bucket = storage_client.get_bucket(config["RESULT_BUCKET"])
        new_blob = src_bucket.copy_blob(src_blob, dest_bucket, file_name)
        src_blob.delete()

    print("""Processed file {} of type {}
    """.format(file_name, content_type))

    if "image" in content_type:
        print(f'Publishing message to topic {config["VISION_TOPIC"]}')
        # References an existing topic
        #topic_path = publisher.topic_path(project_id, config["VISION_TOPIC"])
        topic_path = config["VISION_TOPIC"]

    if "video" in content_type:
        print(f'Publishing message to topic {config["VIDEOINTELLIGENCE_TOPIC"]}')
        # References an existing topic
        topic_path = publisher.topic_path(project_id, config["VIDEOINTELLIGENCE_TOPIC"])


    message_json = json.dumps({
        'contentType' : content_type,
        'gcsUrl' : "gs://" + config['RESULT_BUCKET'] + "/" + file_name,
        'gcsBucket' : config['RESULT_BUCKET'],
        'gcsFile' : file_name
    })
    message_bytes = message_json.encode('utf-8')

    # Publishes the message
    try:
        publish_future = publisher.publish(topic_path, data=message_bytes)
        publish_future.result()  # Verify the publish succeeded
        return 'Message published.'
    except Exception as e:
        print(e)
        return (e, 500)

# Placeholder
def visionAPI():
    return 1

# Placeholder
def videoIntelligenceAPI():
    return 1

# Placeholder
def insertIntoBigQuery():
    return 1
