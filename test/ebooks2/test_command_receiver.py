import base64
import json
import urllib.parse
from unittest import mock
from unittest.mock import Mock

import pytest


def create_event(command):
    body = bytes(urllib.parse.urlencode(command), 'utf-8')
    return {'body': str(base64.b64encode(body), 'utf-8'),
            'isBase64Encoded': True}


def create_mock_queue(mock_boto3):
    mock_sqs = Mock()
    mock_queue = Mock()
    mock_queue.send_message.return_value = {'MessageId': 'message-id'}
    mock_sqs.Queue.return_value = mock_queue
    mock_boto3.resource.return_value = mock_sqs

    return mock_sqs, mock_queue


@mock.patch.dict('os.environ', {'QUEUE_URL': 'queue_url'})
@mock.patch('ebooks2.command_receiver.boto3')
def test_handler(mock_boto3):
    mock_sqs, mock_queue = create_mock_queue(mock_boto3)

    from ebooks2.command_receiver import handler

    command = {'channel_id': 'D1MCER747',
               'channel_name': 'directmessage',
               'command': '/ebooks',
               'response_url': '<response_url>',
               'team_domain': 'sthlm-beers',
               'team_id': 'T1BPCU332',
               'token': 'token',
               'user_id': 'U1BUTMX6K',
               'user_name': 'td'}
    event = create_event(command)

    response = handler(event, Mock())
    assert response == {'statusCode': 200}

    mock_sqs.Queue.asser_called_once_with('queue_url')
    mock_queue.send_message.assert_called_once_with(
        MessageBody=json.dumps(command))
