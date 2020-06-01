import os
import os.path
import shlex
import subprocess
from datetime import datetime, timezone
from io import BytesIO
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import boto3


def zip_directory(directory, prefix='.'):
    def zip_directory_inner(zip_file, directory):
        for filename in os.listdir(directory):
            filename = os.path.join(directory, filename)
            if '__pycache__' in filename:
                continue
            elif os.path.isdir(filename):
                zip_directory_inner(zip_file, filename)
            else:
                arcname = os.path.normpath(os.path.join(prefix, filename))
                print(f'adding {filename} as {arcname}')
                zip_file.write(filename, arcname)

    archive = BytesIO()
    with ZipFile(archive, 'w') as zip_file:
        zip_directory_inner(zip_file, directory)

    archive.seek(0)
    return archive


def zip_dependencies():
    requirements = f'{os.getcwd()}/ebooks2/requirements.txt'

    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        cmd = f'pip install --no-cache-dir -q -r "{requirements}" -t .'
        subprocess.run(shlex.split(cmd))

        return zip_directory('.', prefix='python')


def zip_functions():
    print(os.getcwd())
    return zip_directory('ebooks2')


class Updater:
    def __init__(self, function_names, *, bucket, lambda_):
        self.function_names = function_names

        self.bucket = bucket
        self.lambda_ = lambda_

    def get_dependencies_layer(self, name):
        layers = self.lambda_.list_layers()['Layers']
        return [l for l in layers if l['LayerName'] == name][0]

    def get_functions(self):
        functions = self.lambda_.list_functions()['Functions']
        return [f for f in functions if f['FunctionName'] in self.function_names]

    def update_dependencies_layer(self, layer_name, force=False):
        KEY = 'code/dependencies.zip'

        # get mtime of latest layer version
        try:
            layer = self.get_dependencies_layer(layer_name)
            layer_version = layer['LatestMatchingVersion']
            layer_mtime = datetime.strptime(layer_version['CreatedDate'],
                                            '%Y-%m-%dT%H:%M:%S.%f%z')
        except:
            layer_mtime = None

        # get mtime of requirements.txt
        stat_result = os.stat('ebooks2/requirements.txt')
        localtz = datetime.now().astimezone().tzinfo
        requirements_mtime = datetime.fromtimestamp(stat_result.st_mtime,
                                                    tz=localtz)

        if force or not layer_mtime or layer_mtime < requirements_mtime:
            print('building dependencies.zip')
            zip_file = zip_dependencies()

            print('uploading dependencies.zip')
            self.bucket.upload_fileobj(zip_file, KEY)

            if layer_mtime:
                print('publishing new layer version')
                self.lambda_.publish_layer_version(
                    LayerName=layer_name,
                    Content={'S3Bucket': self.bucket.name,
                             'S3Key': KEY})

                print('fetching new layer version')
                layer = self.get_dependencies_layer(layer_name)
                layer_version = layer['LatestMatchingVersion']
                layer_version_arn = layer_version['LayerVersionArn']

                for function_name in self.function_names:
                    print(f'updating function configuration: {function_name}')
                    self.lambda_.update_function_configuration(
                        FunctionName=function_name,
                        Layers=[layer_version_arn])

        print('dependencies up-to-date')

    def update_function_code(self):
        KEY = 'code/functions.zip'

        # functions = self.get_functions()

        print('building functions.zip')
        zip_file = zip_functions()

        print('uploading functions.zip')
        self.bucket.upload_fileobj(zip_file, KEY)

        for function_name in self.function_names:
            print(f'updating function {function_name}')
            self.lambda_.update_function_code(
                FunctionName=function_name,
                S3Bucket=self.bucket.name,
                S3Key=KEY)

        print('functions up-to-date')


if __name__ == '__main__':
    updater = Updater(['ebooks-command-handler',
                       'ebooks-command-receiver',
                       'ebooks-event-handler',
                       'ebooks-event-receiver'],
                      bucket=boto3.resource('s3').Bucket('steve-ebooks'),
                      lambda_=boto3.client('lambda'),)
    updater.update_dependencies_layer('ebooks-dependencies')
    updater.update_function_code()
