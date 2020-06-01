from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import core
from aws_cdk.aws_lambda import Code

from .stacks import *

app = core.App()

environment = core.Environment(account='079811619059', region='eu-west-1')

bucket_stack = BucketStack(app, 'ebooks-bucket',
                           env=environment,
                           bucket_name='steve-ebooks')

dependencies_code = Code.from_bucket(bucket_stack.bucket,
                                     'code/dependencies.zip')
dependencies_stack = DependenciesStack(app, 'ebooks-dependencies',
                                       env=environment,
                                       layer_code=dependencies_code,
                                       layer_name='ebooks-dependencies')

function_code = Code.from_bucket(bucket_stack.bucket,
                                 'code/functions.zip')

api_stack = UnfortunateApiStack(
    app, 'ebooks-api',
    env=environment,
    api_name='ebooks-api',
    bucket=bucket_stack.bucket,
    domain_name='spookyhouse.co.uk',
    functions=[
        Function(
            id_prefix='Command',
            api_method=apigw.HttpMethod.POST,
            api_path='/command',
            function_code=function_code,
            function_dependencies_layer=dependencies_stack.dependencies_layer,
            function_name_prefix='ebooks-command',
            handler_function_handler='ebooks2.command_handler.handler',
            receiver_function_handler='ebooks2.command_receiver.handler',
            queue_name='ebooks-commands'),
        Function(
            id_prefix='Event',
            api_method=apigw.HttpMethod.POST,
            api_path='/event',
            function_code=function_code,
            function_dependencies_layer=dependencies_stack.dependencies_layer,
            function_name_prefix='ebooks-event',
            handler_function_handler='ebooks2.event_handler.handler',
            receiver_function_handler='ebooks2.event_receiver.handler',
            queue_name='ebooks-events')],
    subdomain='ebooks')
