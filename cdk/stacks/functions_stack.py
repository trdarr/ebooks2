from dataclasses import dataclass

from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from aws_cdk import core
from aws_cdk.aws_lambda_event_sources import ApiEventSource, SqsEventSource


# create two lambdas to handle requests to an endpoint
# 1. the receiver function enqueues messages and responds
# 2. the handler function processes the enqueued messages
class FunctionsStack(core.Stack):
    def __init__(self, scope: core.Construct, stack_id: str, *,
                 env: core.Environment,
                 api_method: apigw.HttpMethod,
                 api_path: str,
                 function_code: lambda_.Code,
                 function_dependencies_layer: lambda_.LayerVersion,
                 function_name_prefix: str,
                 handler_function_handler: str,
                 receiver_function_handler: str,
                 queue_name: str,
                 **kwargs):
        super().__init__(scope, stack_id, env=env, **kwargs)

        # create the queue
        self.queue = sqs.Queue(
            self, 'Queue',
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=1,
                queue=sqs.Queue(
                    self,
                    f'DLQ',
                    queue_name=f'{queue_name}-dlq')),
            queue_name=queue_name)

        # create the receiver function
        # add the queue url as an environment variable
        self.receiver_function = lambda_.Function(
            self, 'ReceiverFunction',
            code=function_code,
            environment={'QUEUE_URL': self.queue.queue_url},
            function_name=f'{function_name_prefix}-receiver',
            handler=receiver_function_handler,
            layers=[function_dependencies_layer],
            # memory_size=256,
            runtime=lambda_.Runtime.PYTHON_3_8)

        # allow the receiver function to enqueue messages
        self.queue.grant_send_messages(self.receiver_function)

        # route requests to the receiver lambda
        # (with a circular dependency, so never mind)
        # api.add_routes(
        #     integration=apigw.LambdaProxyIntegration(
        #         handler=self.receiver_function),
        #     methods=[api_method],
        #     path=api_path)

        # route requests to the receiver lambda
        # (without creating a circular dependency?)
        # integration = apigw.CfnIntegration(
        #     self, 'Integration',
        #     api_id=api.http_api_id,
        #     integration_type='AWS_PROXY',
        #     integration_uri=self.receiver_function.function_arn,
        #     payload_format_version='2.0')

        # apigw.CfnRoute(self, 'Route',
        #                api_id=api.http_api_id,
        #                route_key=f'{api_method.value} {api_path}',
        #                target=f'integrations/{integration.ref}')

        # # trigger the lambda with those routed requests
        # lambda_.CfnEventSourceMapping(
        #     self, 'Mappping',
        #     event_source_arn=f'arn:aws:execute-api:{env.region}:{env.account}:{api.http_api_id}/*/*{api_path}',
        #     function_name=self.receiver_function.function_arn)

        # create the handler function
        self.handler_function = lambda_.Function(
            self, 'HandlerFunction',
            code=function_code,
            function_name=f'{function_name_prefix}-handler',
            handler=handler_function_handler,
            layers=[function_dependencies_layer],
            # memory_size=256,
            runtime=lambda_.Runtime.PYTHON_3_8)

        # add the queue as a trigger for the handler function
        self.handler_function.add_event_source(SqsEventSource(self.queue))
