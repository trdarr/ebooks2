import itertools
import json
import zipfile
from io import BytesIO
from zipfile import ZipFile

import boto3
from markovify import NewlineText

MESSAGES = MODEL = 'm'


# return a dict of users (by id) from users.json
# add a 'MESSAGES' list for message history (later)
def process_users(zip_file):
    users = {}
    with zip_file.open('users.json') as users_file:
        for user in json.load(users_file):
            user[MESSAGES] = []
            user_id = user['id']
            users[user_id] = user
    return users


# return a dict of channels (by name) from channels.json
def process_channels(zip_file):
    channels = {}
    with zip_file.open('channels.json') as channels_file:
        for channel in json.load(channels_file):
            channel_name = channel['name']
            channels[channel_name] = channel
    return channels


# add messages to user objects from history files
def process_messages(zip_file, users, channels):
    # group <channel_name>/<date>.json files by channel name
    groups = itertools.groupby(zip_file.namelist(),
                               key=lambda e: e.split('/')[0])

    for directory, filenames in groups:
        # skip users.json, channels.json, etc.
        if directory not in channels:
            continue

        for filename in filenames:
            # skip directories (<channel_name>/)
            # zip files don't have real directories
            if zip_file.getinfo(filename).is_dir():
                continue

            with zip_file.open(filename) as messages_file:
                for message in json.load(messages_file):
                    # skip messages:
                    #   that have a subtype (channel_join, etc.)
                    #   that have no text (idk really, files maybe?)
                    if 'subtype' in message or not message['text']:
                        continue

                    # skip messages from non-users (bots?)
                    user_id = message['user']
                    user = users.get(user_id)
                    if not user:
                        continue

                    # append the message to the user's messages
                    user[MESSAGES].append(message['text'])


# return a dict of users (by id) with models
# remove users with no messages (so no model)
# replace user[MESSAGES] with user[MODEL]
def train_models(users):
    users = dict(filter(lambda u: u[1][MESSAGES], users.items()))
    for user_id, user in users.items():
        model = NewlineText('\n'.join(user[MESSAGES]),
                            retain_original=False)
        users[user_id][MODEL] = model
    return users


def process_export(filename):
    with ZipFile(filename) as zip_file:
        users = process_users(zip_file)
        channels = process_channels(zip_file)
        process_messages(zip_file, users, channels)

    return train_models(users)


def jumpstart(team_id, filename):
    bucket = boto3.resource('s3').Bucket('steve-ebooks')

    user_models = process_export(filename)
    for user_id, user in user_models.items():
        model_json = user[MODEL].chain.to_json()
        model = BytesIO(bytes(model_json, 'utf-8'))
        key = f'models/{team_id}/{user_id}.json'

        print(f'uploading {key}')
        bucket.upload_fileobj(model, key)


if __name__ == '__main__':
    jumpstart('T1BPCU332', 'export.zip')
