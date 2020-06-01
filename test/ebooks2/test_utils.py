import zlib
from unittest import mock
from unittest.mock import Mock

from markovify import NewlineText

from ebooks2.utils import get_compressed_model, get_model


@mock.patch.object(NewlineText, 'from_chain')
def test_get_model(mock_from_chain):
    def download_fileobj(key, fileobj):
        fileobj.write(b'data')

    mock_bucket = Mock()
    mock_bucket.download_fileobj.side_effect = download_fileobj

    get_model(mock_bucket, 'team_id', 'user_id')

    mock_from_chain.assert_called_once_with('data')


@mock.patch.object(NewlineText, 'from_chain')
def test_get_compressed_model(mock_from_chain):
    def download_fileobj(key, fileobj):
        fileobj.write(zlib.compress(b'data'))

    mock_bucket = Mock()
    mock_bucket.download_fileobj.side_effect = download_fileobj

    get_compressed_model(mock_bucket, 'team_id', 'user_id')

    mock_from_chain.assert_called_once_with('data')
