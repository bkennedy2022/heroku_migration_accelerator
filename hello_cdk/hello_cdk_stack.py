from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core

from aws_cdk import aws_s3 as s3
from aws_cdk import aws_apprunner as apprunner
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticbeanstalk as eb
import json


class HelloCdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get app data from json
        f = open('app.json',)
        data = json.load(f)
        f.close()

        apprunner_service_name = cdk.CfnParameter(self, "ServiceName", type = "String", description = "name of apprunner service", default = data['appName'])

        # VPC
        vpc = ec2.Vpc.from_lookup(self, data["vpcName"], is_default=True)

        # # security group to allow public access
        dbSecurityGroup = ec2.SecurityGroup(self, "PublicAccessDB", vpc=vpc)
        dbSecurityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(5432))

        # Database
        instance = rds.DatabaseInstance(self, 'Instance', \
            engine = rds.DatabaseInstanceEngine.POSTGRES, \
            vpc = vpc, \
            vpc_subnets = ec2.SubnetSelection(subnet_type = ec2.SubnetType.PUBLIC), \
            multi_az = True, \
            security_groups = [dbSecurityGroup]
        )
        
        # Apprunner
        if data['hasGithub'] == 'y':
            app = apprunner.CfnService(self, "Service", \
                service_name = apprunner_service_name.value_as_string, \
                source_configuration = apprunner.CfnService.SourceConfigurationProperty( \
                    code_repository = apprunner.CfnService.CodeRepositoryProperty( \
                        repository_url = data['link'], \
                        source_code_version = apprunner.CfnService.SourceCodeVersionProperty( \
                            type = "BRANCH", \
                            value = "master" \
                        ) \
                    ), \
                    authentication_configuration = apprunner.CfnService.AuthenticationConfigurationProperty( \
                        connection_arn = data['connectionArn'] \
                    ) \
                ) \
            )
        else: 
            app = apprunner.CfnService(self, "Service", \
                service_name = apprunner_service_name.value_as_string, \
                source_configuration = apprunner.CfnService.SourceConfigurationProperty( \
                    image_repository = apprunner.CfnService.ImageRepositoryProperty( \
                        image_identifier = data["link"], \
                        image_configuration = apprunner.CfnService.ImageConfigurationProperty(port = '8000'), \
                        image_repository_type = data['private_or_public'] \
                    ) \
                ) \
            )

        outputs = cdk.CfnOutput(self, "Endpoint", \
            description = "The endpoint of the App Runner service.", \
            value = app.get_att('ServiceUrl').to_string() \
        )
            

        