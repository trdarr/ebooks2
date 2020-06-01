from dataclasses import dataclass

from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sqs as sqs
from aws_cdk import core
from aws_cdk.aws_lambda_event_sources import SqsEventSource

from .api_stack import ApiGatewayV2Domain


@dataclass
class Function:
    id_prefix: str
    api_method: apigw.HttpMethod
    api_path: str
    function_code: lambda_.Code
    function_dependencies_layer: lambda_.LayerVersion
    function_name_prefix: str
    handler_function_handler: str
    receiver_function_handler: str
    queue_name: str


class UnfortunateApiStack(core.Stack):
    def __init__(self,
                 scope: core.Construct,
                 stack_id: str,
                 *,
                 api_name: str,
                 bucket: s3.Bucket,
                 domain_name: str,
                 functions,
                 subdomain: str,
                 **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        hosted_zone = route53.HostedZone.from_lookup(
            self,
            'HostedZone',
            domain_name=domain_name)

        subdomain = f'{subdomain}.{hosted_zone.zone_name}'

        certificate = acm.DnsValidatedCertificate(
            self,
            'Certificate',
            domain_name=subdomain,
            hosted_zone=hosted_zone)

        self.api = apigw.HttpApi(self, 'HttpApi', api_name=api_name)

        domain_name = apigw.CfnDomainName(
            self,
            'DomainName',
            domain_name=subdomain,
            domain_name_configurations=[
                apigw.CfnDomainName.DomainNameConfigurationProperty(
                    certificate_arn=certificate.certificate_arn)])

        # add an alias to the hosted zone
        route53.ARecord(
            self,
            'ARecord',
            record_name=subdomain,
            target=route53.RecordTarget.from_alias(
                ApiGatewayV2Domain(domain_name)),
            zone=hosted_zone)

        mapping = apigw.CfnApiMapping(
            self,
            'ApiMapping',
            api_id=self.api.http_api_id,
            domain_name=domain_name.ref,
            stage='$default')

        mapping.add_depends_on(domain_name)

        for function in functions:
            self.add_endpoint(bucket, function)

    def add_endpoint(self, bucket: s3.Bucket, fn: Function):
        # create the queue
        queue = sqs.Queue(
            self, f'{fn.id_prefix}Queue',
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,
                queue=sqs.Queue(
                    self, f'{fn.id_prefix}DLQ',
                    queue_name=f'{fn.queue_name}-dlq')),
            queue_name=fn.queue_name)

        # create the receiver function
        # add the queue url as an environment variable
        receiver_function = lambda_.Function(
            self, f'{fn.id_prefix}ReceiverFunction',
            code=fn.function_code,
            environment={'QUEUE_URL': queue.queue_url},
            function_name=f'{fn.function_name_prefix}-receiver',
            handler=fn.receiver_function_handler,
            layers=[fn.function_dependencies_layer],
            # memory_size=256,
            runtime=lambda_.Runtime.PYTHON_3_8)

        # allow the receiver function to enqueue messages
        queue.grant_send_messages(receiver_function)

        # route requests to the receiver lambda
        self.api.add_routes(
            integration=apigw.LambdaProxyIntegration(
                handler=receiver_function),
            methods=[fn.api_method],
            path=fn.api_path)

        # create the handler function
        # add the bucket name as an environment variable
        handler_function = lambda_.Function(
            self, f'{fn.id_prefix}HandlerFunction',
            code=fn.function_code,
            environment={'BUCKET_NAME': bucket.bucket_name},
            function_name=f'{fn.function_name_prefix}-handler',
            handler=fn.handler_function_handler,
            layers=[fn.function_dependencies_layer],
            # memory_size=256,
            runtime=lambda_.Runtime.PYTHON_3_8)

        # add the queue as a trigger for the handler function
        handler_function.add_event_source(SqsEventSource(queue))

        # allow the handler function to access the bucket
        bucket.grant_read_write(handler_function)
