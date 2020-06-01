from typing import List

import jsii
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_sqs as sqs
from aws_cdk import core
from aws_cdk.aws_lambda_event_sources import SqsEventSource

from .functions_stack import FunctionsStack


class ApiStack(core.Stack):
    def __init__(self,
                 scope: core.Construct,
                 stack_id: str,
                 *,
                 api_name: str,
                 domain_name: str,
                 functions_stacks: List[FunctionsStack],
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

        for functions_stack in functions_stacks:
            self.api.add_routes(
                integration=apigw.LambdaProxyIntegration(
                    handler=functions_stack.receiver_function),
                methods=[functions_stack.api_method],
                path=functions_stack.api_path)


# necessary because of reasons
@ jsii.implements(route53.IAliasRecordTarget)
class ApiGatewayV2Domain:
    def __init__(self, domain_name):
        self.domain_name = domain_name

    def bind(self, _record):
        return route53.AliasRecordTargetConfig(
            dns_name=self.domain_name.attr_regional_domain_name,
            hosted_zone_id=self.domain_name.attr_regional_hosted_zone_id)
