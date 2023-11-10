import json
from dataclasses import dataclass, field
from pathlib import Path

from cdktf import Fn, TerraformOutput
from cdktf_cdktf_provider_aws.alb import Alb
from cdktf_cdktf_provider_aws.alb_listener import (
    AlbListener,
    AlbListenerDefaultAction,
    AlbListenerDefaultActionForward,
)
from cdktf_cdktf_provider_aws.alb_listener_rule import AlbListenerRule
from cdktf_cdktf_provider_aws.alb_target_group import AlbTargetGroup
from cdktf_cdktf_provider_aws.alb_target_group_attachment import (
    AlbTargetGroupAttachment,
)
from cdktf_cdktf_provider_aws.cloudwatch_log_group import CloudwatchLogGroup
from cdktf_cdktf_provider_aws.data_aws_security_group import DataAwsSecurityGroup
from cdktf_cdktf_provider_aws.iam_policy_attachment import IamPolicyAttachment
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.iam_role_policy import IamRolePolicy
from cdktf_cdktf_provider_aws.lambda_function import (
    LambdaFunction,
    LambdaFunctionTracingConfig,
    LambdaFunctionVpcConfig,
)
from cdktf_cdktf_provider_aws.lambda_function_url import LambdaFunctionUrl
from cdktf_cdktf_provider_aws.lambda_permission import LambdaPermission
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.security_group import (
    SecurityGroup,
    SecurityGroupEgress,
    SecurityGroupIngress,
)
from constructs import Construct

ROOTDIR = Path(__file__).parent.parent


class MyRustLambdaRole(IamRole):
    def __init__(self, scope, id, role_name: str, **kwargs):
        super().__init__(
            scope,
            id,
            **kwargs,
            assume_role_policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Principal": {
                                "Service": ["ec2.amazonaws.com", "lambda.amazonaws.com"]
                            },
                            "Effect": "Allow",
                        }
                    ],
                }
            ),
        )
        self.name = role_name
        self.add_policies()

    def add_policies(self):
        """
        IamRolePolicyAttachment(
            self,
            "policy-attachment-ssm-managed-instance",
            policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
            role=self.id,
        )
        IamRolePolicyAttachment(
            self,
            "policy-attachment-cloudwatchagent",
            policy_arn="arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
            role=self.id,
        )
        """

        IamRolePolicy(
            self,
            "inline-policy-s3-access",
            role=self.id,
            name="EC2Access",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["ec2:*"],
                            "Resource": ["*"],
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            "Resource": "*",
                        },
                    ],
                },
            ),
        )


class OffchainMetadataLoadbalancer(Construct):
    """Create the loadbalancer, listener and target groups"""

    security_group: SecurityGroup
    target_group: AlbTargetGroup

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.security_group = SecurityGroup(
            self,
            "security-group",
            name="ShnazzyLoadbalancerSecurityGroup",
            ingress=[
                SecurityGroupIngress(
                    protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"]
                ),
                SecurityGroupIngress(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_blocks=["0.0.0.0/0"],
                ),
            ],
            egress=[
                SecurityGroupEgress(
                    protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"]
                ),
                SecurityGroupEgress(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_blocks=["0.0.0.0/0"],
                ),
            ],
        )
        func_alb = Alb(
            self,
            "loadbalancer",
            name="ShnazzyLoadbalancer",
            subnets=["subnet-1a887171", "subnet-39a89643", "subnet-a056a4ed"],
            security_groups=[self.security_group.id],
        )

        self.target_group = AlbTargetGroup(
            self, "target-group-lambda", target_type="lambda", deregistration_delay="10"
        )

        http_listener = AlbListener(
            self,
            "alb-http-listener",
            load_balancer_arn=func_alb.arn,
            port=80,
            protocol="HTTP",
            default_action=[
                AlbListenerDefaultAction(
                    type="forward",
                    target_group_arn=self.target_group.arn,
                )
            ],
        )


class LambdaFunc(Construct):
    """ """

    def __init__(
        self,
        scope: Construct,
        id: str,
        loadbalancer_target_group: AlbTargetGroup,
        loadbalancer_security_group: SecurityGroup,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        lambda_local_artefact = ROOTDIR.joinpath(
            "offchain-metadata-api/target/lambda/offchain-metadata-api/bootstrap.zip"
        ).as_posix()
        lambda_security_group = SecurityGroup(
            self,
            "security-group",
            name="OffchainMetadaLambdaSecurityGroup",
            ingress=[
                SecurityGroupIngress(
                    protocol="tcp",
                    from_port=80,
                    to_port=80,
                    security_groups=[loadbalancer_security_group.id],
                ),
                SecurityGroupIngress(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    security_groups=[loadbalancer_security_group.id],
                ),
            ],
            egress=[
                SecurityGroupEgress(
                    protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"]
                )
            ],
        )
        lambda_func = LambdaFunction(
            self,
            "lambda-func",
            function_name="ShnazzyMetadataLambda",
            role=OffchainMetadataLambdaRole(self, "lambda-role").arn,
            description="A shnazzy rust lambda",
            handler="bootstrap",
            runtime="provided.al2",
            architectures=["arm64"],
            memory_size=128,
            filename=lambda_local_artefact,
            package_type="Zip",
            # s3_bucket="tf-state-bucket-yie4rae",
            # s3_key="ops-cdktf-offchain-metadata-lambda/offchain-metadata-lambda-stack/lambda.zip",
            # s3_object_version="",
            source_code_hash=Fn.filebase64sha256(lambda_local_artefact),
            tracing_config=LambdaFunctionTracingConfig(mode="PassThrough"),
            vpc_config=LambdaFunctionVpcConfig(
                subnet_ids=["subnet-1a887171", "subnet-39a89643", "subnet-a056a4ed"],
                security_group_ids=[lambda_security_group.id],
            ),
        )
        lambda_func_url = LambdaFunctionUrl(
            self,
            "lambda-func-urlendpoint",
            function_name=lambda_func.function_name,
            authorization_type="NONE",
        )
        TerraformOutput(
            self,
            "output-lambdafunc-functionurl",
            value=lambda_func_url.function_url,
        )
        CloudwatchLogGroup(
            self,
            "cloudwatch-log-group",
            name=f"/aws/lambda/{lambda_func.function_name}",
        )
        LambdaPermission(
            self,
            "lambda-lodbalancer-permission",
            action="lambda:InvokeFunction",
            principal="elasticloadbalancing.amazonaws.com",
            function_name=lambda_func.function_name,
            source_arn=loadbalancer_target_group.arn,
        )
        AlbTargetGroupAttachment(
            self,
            "target-group-lambda-attachment",
            target_id=lambda_func.arn,
            target_group_arn=loadbalancer_target_group.arn,
        )


@dataclass
class MyRustLambdaFuncConfig:
    name: str  # Name of the Lambda itself
    bucket_name: str  # Name of the bucket the artefact is stored


class MyRustLambdaFunc(Construct):
    bucket: S3Bucket
    role: MyRustLambdaRole

    def __init__(self, scope, id, config: MyRustLambdaFuncConfig, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.bucket = S3Bucket(self, "", bucket=config.bucket_name)
        self.role = MyRustLambdaRole(self, "rust_lambda_role", role_name=config.name)
