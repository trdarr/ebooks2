from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import Mock

import boto3
import freezegun
import pytest

from deploy import update_dependencies

NOW = datetime.now()


def make_response(created_date):
    return {'Layers': [{'LatestMatchingVersion': {'CompatibleRuntimes': ['python3.8'],
                                                  'CreatedDate': created_date.isoformat(),
                                                  'LayerVersionArn': 'arn:aws:lambda:eu-west-1:079811619059:layer:ebooks-dependencies:1',
                                                  'Version': 1},
                        'LayerArn': 'arn:aws:lambda:eu-west-1:079811619059:layer:ebooks-dependencies',
                        'LayerName': 'ebooks-dependencies'}]}


@freezegun.freeze_time(NOW)
@mock.patch('deploy.boto3')
def test_update_dependencies_outdated(mock_boto3):
    mock_lambda = Mock()
    response = make_response(NOW - timedelta(hours=1))
    mock_lambda.list_layers.return_value = response
    mock_boto3.client.return_value = mock_lambda

    mock_s3 = Mock()
    mock_boto3.resource.return_value = mock_s3

    update_dependencies()


@freezegun.freeze_time(NOW)
@mock.patch('deploy.boto3')
def test_update_dependencies_up_to_date(mock_boto3):
    mock_lambda = Mock()
    response = make_response(NOW)
    mock_lambda.list_layers.return_value = response
    mock_boto3.client.return_value = mock_lambda

    mock_s3 = Mock()
    mock_boto3.resource.return_value = mock_s3

    update_dependencies()


@mock.patch('deploy.boto3')
def test_update_dependencies_force(mock_boto3):
    mock_lambda = Mock()
    response = make_response(NOW - timedelta(hours=1))
    mock_lambda.list_layers.return_value = response
    mock_boto3.client.return_value = mock_lambda

    mock_s3 = Mock()
    mock_boto3.resource.return_value = mock_s3

    update_dependencies()
