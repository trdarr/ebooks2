import base64
import json
import urllib.parse
from unittest import mock
from unittest.mock import Mock


def create_event(event):
    return {'body': json.dumps(event),
            'isBase64Encoded': False}


def create_mock_queue(mock_boto3):
    mock_sqs = Mock()
    mock_queue = Mock()
    mock_queue.send_message.return_value = {'MessageId': 'message-id'}
    mock_sqs.Queue.return_value = mock_queue
    mock_boto3.resource.return_value = mock_sqs

    return mock_sqs, mock_queue


@mock.patch.dict('os.environ', {'QUEUE_URL': 'queue_url'})
@mock.patch('ebooks2.event_receiver.boto3')
def test_handler(mock_boto3):
    mock_sqs, mock_queue = create_mock_queue(mock_boto3)

    from ebooks2.event_receiver import handler

    event = {'team_id': 'T1BPCU332',
             'event': {'type': 'message',
                       'text': 'text',
                       'user': 'U1BUTMX6K',
                       'team': 'T1BPCU332',
                       'channel': 'C4BD5JQLT',
                       'channel_type': 'channel'},
             'type': 'event_callback'}

    response = handler(create_event(event), Mock())
    assert response == {'statusCode': 200}

    mock_sqs.Queue.asser_called_once_with('queue_url')
    mock_queue.send_message.assert_called_once_with(
        MessageBody=json.dumps(event))


@mock.patch.dict('os.environ', {'QUEUE_URL': 'queue_url'})
@mock.patch('ebooks2.event_receiver.boto3')
def test_handler_challenge(mock_boto3):
    from ebooks2.event_receiver import handler

    event = {'challenge': 'challenge',
             'type': 'url_verification'}

    response = handler(create_event(event), Mock())
    assert response == {'body': event['challenge'],
                        'statusCode': 200}
