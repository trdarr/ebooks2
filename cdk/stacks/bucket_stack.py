from aws_cdk import aws_s3 as s3
from aws_cdk import core


class BucketStack(core.Stack):
    def __init__(self, scope, stack_id, *, bucket_name, **kwargs):
        super().__init__(scope, stack_id, **kwargs)

        # shit i forgot we needed a new
        self.bucket = s3.Bucket(
            self,
            'Bucket',
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            bucket_name=bucket_name,
            removal_policy=core.RemovalPolicy.DESTROY)
