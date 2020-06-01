import json
import os

import boto3
import markovify
from markovify import NewlineText

from .utils import get_model, put_model


def handler(event, context):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['BUCKET_NAME'])

    def handle_one(body):
        if 'subtype' in body['event']:
            subtype = body['event']['subtype']
            print(f"ignoring event with subtype {subtype}")
            return

        print(body)

        team_id = body['team_id']
        user_id = body['event']['user']
        channel_id = body['event']['channel']
        text = body['event']['text']

        print(f'message from {user_id} in {channel_id}: {text}')

        old_model = get_model(bucket, team_id, user_id)
        new_model = NewlineText(text, retain_original=False)
        combined = markovify.combine([old_model, new_model])
        put_model(bucket, team_id, user_id, combined)

    for record in event['Records']:
        handle_one(json.loads(record['body']))

    print('done')
    return {'statusCode': 200}
