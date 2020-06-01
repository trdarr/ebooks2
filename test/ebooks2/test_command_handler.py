import json
import os
from unittest import mock
from unittest.mock import Mock

import pytest
from markovify import NewlineText


def create_event(*commands):
    return {'Records': list(map(lambda c: {'body': json.dumps(c)}, commands))}


def create_mock_bucket(mock_boto3):
    mock_s3 = Mock()
    mock_bucket = Mock()
    mock_s3.Bucket.return_value = mock_bucket
    mock_boto3.resource.return_value = mock_s3

    return mock_s3, mock_bucket


@mock.patch.dict('os.environ', {'BUCKET_NAME': 'bucket_name'})
@mock.patch('ebooks2.command_handler.boto3')
@mock.patch.object(NewlineText, 'from_chain')
@mock.patch('ebooks2.command_handler.requests')
def test_handler(mock_requests, mock_from_chain, mock_boto3):
    mock_s3, mock_bucket = create_mock_bucket(mock_boto3)

    mock_model = Mock()
    mock_model.make_sentence.return_value = 'sentence'
    mock_from_chain.return_value = mock_model

    command = {'channel_id': 'D1MCER747',
               'channel_name': 'directmessage',
               'command': '/ebooks',
               'response_url': 'response_url',
               'team_domain': 'sthlm-beers',
               'team_id': 'T1BPCU332',
               'token': 'token',
               'user_id': 'U1BUTMX6K',
               'user_name': 'td'}

    from ebooks2.command_handler import handler

    handler(create_event(command), Mock())

    mock_s3.Bucket.assert_called_once_with('bucket_name')
    mock_bucket.download_fileobj.assert_called_once_with(
        'models/T1BPCU332/U1BN1PX27.json',
        mock.ANY)
    mock_model.make_sentence.assert_called_once_with()
    mock_requests.post.assert_called_once_with(
        'response_url',
        json={'response_type': 'in_channel',
              'text': 'sentence'})


@mock.patch.dict('os.environ', {'BUCKET_NAME': 'bucket_name'})
@mock.patch('ebooks2.command_handler.boto3')
@mock.patch.object(NewlineText, 'from_chain')
@mock.patch('ebooks2.command_handler.requests')
def test_handler_with_user(mock_requests, mock_from_chain, mock_boto3):
    mock_s3, mock_bucket = create_mock_bucket(mock_boto3)

    mock_model = Mock()
    mock_model.make_sentence.return_value = 'sentence'
    mock_from_chain.return_value = mock_model

    command = {'channel_id': 'D1MCER747',
               'channel_name': 'directmessage',
               'command': '/ebooks',
               'response_url': 'response_url',
               'team_domain': 'sthlm-beers',
               'team_id': 'T1BPCU332',
               'text': '<@U1BUTMX6K|td>',
               'token': 'token',
               'user_id': 'U1BUTMX6K',
               'user_name': 'td'}

    from ebooks2.command_handler import handler

    handler(create_event(command), Mock())

    mock_s3.Bucket.assert_called_once_with('bucket_name')
    mock_bucket.download_fileobj.assert_called_once_with(
        'models/T1BPCU332/U1BUTMX6K.json',
        mock.ANY)
    mock_model.make_sentence.assert_called_once_with()
    mock_requests.post.assert_called_once_with(
        'response_url',
        json={'response_type': 'in_channel',
              'text': 'sentence'})


@mock.patch.dict('os.environ', {'BUCKET_NAME': 'bucket_name'})
@mock.patch('ebooks2.command_handler.boto3')
@mock.patch.object(NewlineText, 'from_chain')
@mock.patch('ebooks2.command_handler.requests')
def test_handler_with_nonsense(mock_requests, mock_from_chain, mock_boto3):
    mock_s3, mock_bucket = create_mock_bucket(mock_boto3)

    mock_model = Mock()
    mock_model.make_sentence.return_value = 'sentence'
    mock_from_chain.return_value = mock_model

    command = {'channel_id': 'D1MCER747',
               'channel_name': 'directmessage',
               'command': '/ebooks',
               'response_url': 'response_url',
               'team_domain': 'sthlm-beers',
               'team_id': 'T1BPCU332',
               'text': 'zamazingo',
               'token': 'token',
               'user_id': 'U1BUTMX6K',
               'user_name': 'td'}

    from ebooks2.command_handler import handler

    handler(create_event(command), Mock())

    mock_s3.Bucket.assert_called_once_with('bucket_name')
    mock_bucket.download_fileobj.assert_called_once_with(
        'models/T1BPCU332/U1BN1PX27.json',
        mock.ANY)
    mock_model.make_sentence.assert_called_once_with()
    mock_requests.post.assert_called_once_with(
        'response_url',
        json={'response_type': 'in_channel',
              'text': 'sentence'})
