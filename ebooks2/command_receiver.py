import base64
import json
import os
import urllib.parse

import boto3


def parse_body(event):
    if event['isBase64Encoded']:
        body = str(base64.b64decode(event['body']), 'utf-8')
        return dict(urllib.parse.parse_qsl(body))

    return json.loads(event['body'])


def handler(event, context):
    sqs = boto3.resource('sqs')
    queue = sqs.Queue(os.environ['QUEUE_URL'])

    body = parse_body(event)
    response = queue.send_message(MessageBody=json.dumps(body))
    print(f"enqueued message {response['MessageId']}")

    print('done')
    return {'statusCode': 200}
