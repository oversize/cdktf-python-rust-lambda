#!/usr/bin/env python
"""
You write Stacks to group Resources. Or better Constructs that is!
You can have multiple stacks within one project!
But you only ever deploy one stack!
"""
from dataclasses import dataclass
from cdktf import App, S3Backend, TerraformStack, TerraformVariable
from cdktf_cdktf_provider_aws.provider import AwsProvider
from constructs import Construct

from infra import (
    MyRustLambdaFunc,
    MyRustLambdaFuncConfig,
    OffchainMetadataLoadbalancer,
    OffchainMetadataRegistryBucket,
)


@dataclass
class MyRustLambdaStackConfig:
    pass


class MyRustLambdaStack(TerraformStack):
    """Stack for the offchain metadata api lambda solution.
    Creates:
        * Application Loadbalancer, Target Groups, Listener
        * IAM Role for the lambda
        * The lambda itself (based on ./offchain-metadata-api-lambda)
    """

    def __init__(self, scope: Construct, id: str, config: MyRustLambdaStackConfig):
        super().__init__(scope, id)
        AwsProvider(self, "aws", region="eu-central-1")
        # Enable S3 State
        # S3Backend(self, bucket="XXX", key=f"XXX", region="XXX", dynamodb_table="XXX")
        # The bucket where the Lambda will be deplozed from
        MyRustLambdaFunc(
            self,
            "rust_lambda_func",
            MyRustLambdaFuncConfig(
                name="MyRustLambda",
                other_option=True,
                bucket_name="myrustlambda-cj184xy2",
            ),
        )
        bucket = OffchainMetadataRegistryBucket(self, "s3-bucket")

        lb = OffchainMetadataLoadbalancer(self, "offchain-metadata-loadbalancer")
        func = LambdaFunc(
            self,
            "lambda-func",
            loadbalancer_target_group=lb.target_group,
            loadbalancer_security_group=lb.security_group,
        )


def main():
    app = App(stack_traces=False)
    MyRustLambdaStack(app, "rust_lambda_stack", MyRustLambdaStackConfig())
    app.synth()


if __name__ == "__main__":
    main()
