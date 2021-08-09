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

        # The code that defines your stack goes here

        apprunner_service_name = cdk.CfnParameter(self, "ServiceName", type = "String", description = "name of apprunner service", default = data['appName'])

        # version_name = cdk.TemplateOptions(template_format_version = "2010-09-09")

        # VPC
        # # TODO: VPC name should not be hardcoded. need to get from ID or name that was input
        vpc = ec2.Vpc.from_lookup(self, data["vpcName"], is_default=True)

        # # security group to allow public access
        dbSecurityGroup = ec2.SecurityGroup(self, "PublicAccessDB", vpc=vpc)
        dbSecurityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80)) #should this be TCP or something else? 

        # # subnets
        # # subnet1 = ec2.PublicSubnet(self, "subnet1", vpc_id = "TestVPC", availability_zone = "us-east-1a")
        # # i don't think i need these. the vpc should already have a public subnet in each AZ

        # # Database
        # # TODO: map heroku database size to rds database size
        # # TODO: can I specify Postgres version?
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
                        # code_configuration = apprunner.CfnService.CodeConfigurationProperty
                    ), \
                    # note: connection_arn is required for github repos
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
                        #TODO: Configure this for ECR 
                        image_identifier = data["link"], \
                        image_configuration = apprunner.CfnService.ImageConfigurationProperty(port = '8000'), \
                        #TODO: configure this for private ECR repo (and add option in discovery piece)
                        image_repository_type = data['private_or_public'] \
                    ) \
                ) \
            )

        # app = eb.CfnService(self, data['appName'])

        # env = eb.CfnEnvironment(self, data['appName'], platform_arn = 'platform', )

        # outputs = cdk.CfnOutput(self, "Output", \
        #     endpoint = cdk.CfnOutputProps( \
        #         value = app.get_att('ServiceUrl')
        #     ) \
        # )

        outputs = cdk.CfnOutput(self, "Endpoint", \
            description = "The endpoint of the App Runner service.", \
            value = app.get_att('ServiceUrl').to_string() \
        )
            

        