import zlib
from io import BytesIO

from markovify import NewlineText


def get_model(bucket, team_id, user_id):
    key = f"models/{team_id}/{user_id}.json"
    print(f'downloading model {key}')

    model_json = BytesIO()
    bucket.download_fileobj(key, model_json)
    model = str(model_json.getbuffer(), 'utf-8')
    return NewlineText.from_chain(model)


def get_compressed_model(bucket, team_id, user_id):
    key = f"models/{team_id}/{user_id}.gz"
    print(f'downloading model {key}')

    model_gz = BytesIO()
    bucket.download_fileobj(key, model_gz)
    model = str(zlib.decompress(model_gz.getbuffer()), 'utf-8')
    return NewlineText.from_chain(model)


def put_model(bucket, team_id, user_id, model):
    key = f"models/{team_id}/{user_id}.json"
    print(f'uploading model {key}')

    model_json = bytes(model.chain.to_json(), 'utf-8')
    bucket.upload_fileobj(BytesIO(model_json), key)


def put_compressed_model(bucket, team_id, user_id, model):
    key = f"models/{team_id}/{user_id}.gz"
    print(f'downloading model {key}')

    model_json = bytes(model.chain.to_json(), 'utf-8')
    model_gz = BytesIO(zlib.compress(model_json))
    bucket.upload_fileobj(model_gz, key)
