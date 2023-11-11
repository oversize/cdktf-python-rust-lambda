#!/usr/bin/env python
"""
"""
import os
from pathlib import Path
from cdktf import App, TerraformStack, S3Backend
from cdktf_cdktf_provider_aws.provider import AwsProvider
from constructs import Construct

from infra import (
    SimpleLambdaFunc,
    SimpleLambdaFuncConfig,
)

ROOTDIR = Path(__file__).parent


class MyRustLambdaStack(TerraformStack):
    """Stack that creates some examples for rust lambdas"""

    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        AwsProvider(self, "aws", region="eu-central-1")
        S3Backend(
            self,
            bucket=os.getenv("TFSTATE_BUCKET"),
            key=os.getenv("TFSTATE_KEY"),
            region=os.getenv("AWS_REGION"),
            dynamodb_table=os.getenv("TFSTATE_LOCKTABLE"),
        )

        SimpleLambdaFunc(
            self,
            "simple_lambda",
            SimpleLambdaFuncConfig(
                name="SimpleRustLambda",
                memory=128,
                description="A super simple lambda that does nothing!",
                artefact=ROOTDIR.joinpath(
                    "./lambdas/simplelambda/target/lambda/simplelambda/bootstrap.zip"
                ),
            ),
        )


def main():
    app = App(stack_traces=False)
    MyRustLambdaStack(app, "rust_lambda_stack")
    app.synth()


if __name__ == "__main__":
    main()
