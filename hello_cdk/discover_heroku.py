# discover_heroku.py
import click
import requests
import heroku3
import json
import os
import webbrowser
import re


@click.command()

def main():

    # login to Heroku
    click.secho("Please login to your Heroku account...", fg = 'green')
    os.system("heroku login")

    regionMap = {'us':'us-east-1', 'eu':'eu-west-1'}
    herokuData = {}

    # list customer's apps
    click.secho("Listing apps...", fg = 'green')
    apps = os.system("heroku apps")

    # get app name to migrate
    appName = click.prompt(click.style("Enter name of app you'd like to migrate", fg = 'blue'))
    herokuData['appName'] = appName

    # get app info
    click.secho("Getting app info...", fg = 'green')
    r=requests.get("https://api.heroku.com/apps/"+appName, headers={"Accept":"application/vnd.heroku+json; version=3"})
    jsonResponse = json.loads(r.content.decode('utf-8'))
    print(jsonResponse)

    # entered an invalid app name
    try:
        aws_region = jsonResponse['region']['name']
    except KeyError: 
        click.secho("No app with that name.", fg = 'red')
        return

    # map app region
    click.secho("Your app's region is", fg = 'green')
    click.echo(aws_region)
    click.secho("For the fastest data replication, this will map to the AWS region ", fg = 'green')
    click.echo(regionMap[aws_region])
    herokuData['region'] = regionMap[aws_region]

    # dyno info
    d=requests.get("https://api.heroku.com/apps/"+appName+"/dynos", headers={"Accept":"application/vnd.heroku+json; version=3"})
    dynos = json.loads(d.content.decode('utf-8'))
    click.secho("Dyno info:", fg = 'green')
    click.echo(dynos)

    # list add-ons
    click.secho("Listing addons...", fg = 'green')
    os.system("heroku addons")

    # get database version
    databaseInfo = os.popen("heroku pg:info").read() # need to modify this for case when user has multiple apps on account
    databaseVersion = re.search("1?[0-9][.][0-9][0-9]?", databaseInfo).group()
    herokuData['PG_Version'] = databaseVersion

    # configure access to AWS account
    os.system("aws configure set default.region "+regionMap[aws_region])
    click.secho("You'll need to create an IAM user with administrator access to deploy your AWS services. Follow the instructions \
    in this tool's documentation to create this user. When you've finished, enter the user's Access Key ID and Secret Access Key below. \
    ", fg = 'green')
    aws_access_key_id = click.prompt(click.style("AWS Access Key ID", fg = 'blue'))
    aws_secret_access_key = click.prompt(click.style("AWS Secret Access Key", fg = 'blue'))
    os.system("aws configure set aws_access_key_id "+aws_access_key_id)
    os.system("aws configure set aws_secret_access_key "+aws_secret_access_key)
    
    # launch VPC
    if aws_region == 'us':
        response = click.prompt(click.style("About to launch browser window. Follow instructions to launch VPC and return to terminal when completed. Press enter to proceed", fg = 'blue'), default="", show_default=False)       
        webbrowser.open("https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateURL=https://s3.amazonaws.com/awslabs-startup-kit-templates-deploy-v5/vpc.cfn.yml", new=1, autoraise=True)
    elif aws_region == 'eu':
        response = click.prompt(click.style("About to launch browser window. Follow instructions to launch VPC and return to terminal when completed. Press enter to proceed", fg = 'blue'), default="", show_default=False)
        webbrowser.open("https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/review?templateURL=https://s3.amazonaws.com/awslabs-startup-kit-templates-deploy-v5/vpc.cfn.yml", new=1, autoraise=True)
    else:
        click.secho("No region specified... cannot proceed", fg = 'blue')
        return
    herokuData['vpcName'] = click.prompt(click.style("Enter name of your new VPC", fg = 'blue'))

    # get repo
    hasGithub = click.prompt(click.style("Do you have a github repo? Enter y/n", fg = 'blue'))
    while (hasGithub != 'y' and hasGithub != 'n'):
        hasGithub = click.prompt(click.style("Do you have a github repo? Enter y/n", fg = 'blue'))
    herokuData['hasGithub'] = hasGithub
    if (hasGithub == 'y'):
        herokuData['link'] = click.prompt(click.style("Enter your repo link", fg = 'blue'))
        
        # create github connection
        conn = os.popen("aws apprunner create-connection --connection-name \"apprunner-github-connection\" --provider-type \"GITHUB\"").read()
        connJson = json.loads(conn)
        herokuData["connectionArn"] = connJson['Connection']['ConnectionArn']
    else:
        hasECR = click.prompt(click.style("Do you have an Amazon ECR URI? Enter y/n", fg = 'blue'))
        while (hasECR != 'y' and hasECR != 'n'):
            hasECR = click.prompt(click.style("Do you have an Amazon ECR URI? Enter y/n", fg = 'blue'))
        herokuData['hasECR'] = hasECR
        if (hasECR == 'y'):
            herokuData['link'] = click.prompt(click.style("Enter your URI", fg = 'blue'))
            private_or_public = click.prompt(click.style("Is your ECR repo private or public? Enter 'private' or 'public' ", fg = 'blue'))
            while (private_or_public != 'private' and private_or_public != 'public'):
                private_or_public = click.prompt(click.style("Please enter 'private' or 'public'", fg = 'blue'))
            if (private_or_public == 'private'):
                herokuData['private_or_public'] = 'ECR'
            else:
                herokuData['private_or_public'] = 'ECR_PUBLIC'
        else:
            click.secho("Please either upload your code to github or your container to ECR.", fg = 'green')
            return

    # get AWS account ID
    awsAccountID = os.popen("aws sts get-caller-identity --query Account --output text").read()
    herokuData['AWS_ID'] = awsAccountID.strip('\n')

    # save data in json file
    json_object = json.dumps(herokuData, indent = 4)
    with open("app.json", "w") as outfile:
        outfile.write(json_object)

    # synthesize cloudformation template
    click.secho("Synthesizing your cloudformation template...", fg = 'green')    
    os.system("cdk synth --trace")

    # deploy template
    deploy = click.prompt(click.style("Deploy this template to your AWS account? Enter y/n", fg = 'blue'))   
    while (deploy != 'y' and deploy != 'n'): 
        deploy = click.prompt(click.style("Deploy this template to your AWS account? Enter y/n", fg = 'blue'))   
    if (deploy == 'y'):
        click.secho("Deploying your cloudformation template...", fg = 'green')
        os.system("cdk deploy --debug")

if __name__ == "__main__":
    main()

    