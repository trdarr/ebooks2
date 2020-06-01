import json
import os
import re
import zlib
from io import BytesIO

import boto3
import requests
from markovify import NewlineText

from .utils import get_model

USER_ID_RE = re.compile(r'^<@(U\w+)\|([^>]+)>$')
DEFAULT_USER_ID = 'U1BN1PX27'
DEFAULT_USER_NAME = 'steve'


def handler(event, command):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['BUCKET_NAME'])

    def handle_one(command):
        match = USER_ID_RE.match(command.get('text', ''))
        if match:
            user_id, user_name = match.groups()
        else:
            user_id = DEFAULT_USER_ID
            user_name = DEFAULT_USER_NAME

        request_user = f"<@{command['user_id']}|{command['user_name']}>"
        request_channel = f"<#{command['channel_id']}|{command['channel_name']}>"
        print(
            f"request from {request_user} in {request_channel}:"
            f" {command['command']} {command.get('text', '')}")

        sentence = get_model(bucket,
                             command['team_id'],
                             user_id).make_sentence()
        print(f"generated sentence for <@{user_id}|{user_name}>: {sentence}")

        requests.post(command['response_url'],
                      json={'response_type': 'in_channel',
                            'text': sentence})

    for record in event['Records']:
        handle_one(json.loads(record['body']))

    print('done')
