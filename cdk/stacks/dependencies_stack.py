from aws_cdk import aws_lambda as lambda_
from aws_cdk import core


class DependenciesStack(core.Stack):
    def __init__(self,
                 scope: core.Construct,
                 stack_id: str,
                 *,
                 layer_code: lambda_.Code,
                 layer_name: str,
                 **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        self.dependencies_layer = lambda_.LayerVersion(
            self,
            'DependenciesLayer',
            code=layer_code,
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_8],
            layer_version_name=layer_name)
