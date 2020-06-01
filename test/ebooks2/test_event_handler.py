import json
from unittest import mock
from unittest.mock import Mock


def create_event(*events):
    return {'Records': list(map(lambda e: {'body': json.dumps(e)}, events))}


def create_mock_bucket(mock_boto3):
    mock_s3 = Mock()
    mock_bucket = Mock()
    mock_s3.Bucket.return_value = mock_bucket
    mock_boto3.resource.return_value = mock_s3

    return mock_s3, mock_bucket


@mock.patch.dict('os.environ', {'BUCKET_NAME': 'bucket_name'})
@mock.patch('ebooks2.event_handler.boto3')
@mock.patch('ebooks2.event_handler.markovify')
@mock.patch('ebooks2.event_handler.get_model')
@mock.patch('ebooks2.event_handler.put_model')
def test_handler(mock_put_model, mock_get_model, mock_markovify, mock_boto3):
    mock_s3, _ = create_mock_bucket(mock_boto3)

    mock_model = Mock()
    mock_model.to_json = ''
    mock_get_model.return_value = mock_model

    event = {'team_id': 'T1BPCU332',
             'event': {'type': 'message',
                       'text': 'text',
                       'user': 'U1BUTMX6K',
                       'team': 'T1BPCU332',
                       'channel': 'C4BD5JQLT',
                       'channel_type': 'channel'},
             'type': 'event_callback'}

    from ebooks2.event_handler import handler

    handler(create_event(event), Mock())

    mock_s3.Bucket.assert_called_once_with('bucket_name')
    mock_get_model.assert_called_once()
    mock_markovify.combine.assert_called_once()
    mock_put_model.assert_called_once()
