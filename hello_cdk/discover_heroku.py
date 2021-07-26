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

    # addonInfo = os.popen("heroku addons").read()
    # # addonInfo = os.system("heroku addons")
    # print(addonInfo)

    # TODO: uncomment this
    # os.system("heroku login")

    regionMap = {'us':'us-east-1', 'eu':'eu-west-1'}
    herokuData = {}

    click.secho("Listing apps...", fg = 'green')
    apps = os.system("heroku apps")

    # get app name
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

    # TODO: get addons
    click.secho("Listing addons...", fg = 'green')
    os.system("heroku addons")

    # get database version
    # TODO: do i need this???
    databaseInfo = os.popen("heroku pg:info").read() # need to modify this for case when user has multiple apps on account
    databaseVersion = re.search("1?[0-9][.][0-9][0-9]?", databaseInfo).group()
    herokuData['PG_Version'] = databaseVersion

    # os.system("aws configure")

    # launch VPC
    # TODO: UNCOMMENT THIS
    # TODO: add guidance about availability zones
    # if aws_region == 'us':
    #     response = click.prompt(click.style("About to launch browser window. Follow instructions to launch VPC and return to terminal when completed. Press enter to proceed", fg = 'blue'), default="", show_default=False)       
    #     webbrowser.open("https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateURL=https://s3.amazonaws.com/awslabs-startup-kit-templates-deploy-v5/vpc.cfn.yml", new=1, autoraise=True)
    # elif aws_region == 'eu':
    #     response = click.prompt(click.style("About to launch browser window. Follow instructions to launch VPC and return to terminal when completed. Press enter to proceed", fg = 'blue'), default="", show_default=False)
    #     webbrowser.open("https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/review?templateURL=https://s3.amazonaws.com/awslabs-startup-kit-templates-deploy-v5/vpc.cfn.yml", new=1, autoraise=True)
    # else:
    #     click.secho("No region specified... cannot proceed", fg = 'blue')
    #     return
    # TODO: we need the name, not the ID...
    # herokuData['vpcID'] = click.prompt(click.style("Enter ID of your new VPC", fg = 'blue'))

    # get repo
    hasGithub = click.prompt(click.style("Do you have a github repo? Enter y/n", fg = 'blue'))
    while (hasGithub != 'y' and hasGithub != 'n'):
        hasGithub = click.prompt(click.style("Do you have a github repo? Enter y/n", fg = 'blue'))
    herokuData['hasGithub'] = hasGithub
    if (hasGithub == 'y'):
        herokuData['link'] = click.prompt(click.style("Enter your repo link", fg = 'blue'))
    else:
        hasECR = click.prompt(click.style("Do you have an Amazon ECR URI? Enter y/n", fg = 'blue'))
        while (hasECR != 'y' and hasECR != 'n'):
            hasECR = click.prompt(click.style("Do you have an Amazon ECR URI? Enter y/n", fg = 'blue'))
        herokuData['hasECR'] = hasECR
        if (hasECR == 'y'):
            herokuData['link'] = click.prompt(click.style("Enter your URI", fg = 'blue'))
        else:
            click.secho("Please either upload your code to github or your container to ECR.", fg = 'green')
            return

    # get AWS account ID
    awsAccountID = os.popen("aws sts get-caller-identity --query Account --output text").read()
    herokuData['AWS_ID'] = awsAccountID.strip('\n')

    # create github connection
    conn = os.popen("aws apprunner create-connection --connection-name \"apprunner-github-connection\" --provider-type \"GITHUB\"").read()
    print(conn)
    connJson = json.loads(conn)
    print(connJson)
    herokuData["connectionArn"] = connJson['Connection']['ConnectionArn']

    # save data in json file
    json_object = json.dumps(herokuData, indent = 4)
    with open("app.json", "w") as outfile:
        outfile.write(json_object)


    click.secho("Synthesizing your cloudformation template...", fg = 'green')    
    os.system("cdk synth --trace")

    deploy = click.prompt(click.style("Deploy this template to your AWS account? Enter y/n", fg = 'blue'))   
    while (deploy != 'y' and hasECR != 'n'): 
        deploy = click.prompt(click.style("Deploy this template to your AWS account? Enter y/n", fg = 'blue'))   
    click.secho("Deploying your cloudformation template...", fg = 'green')
    os.system("cdk deploy --debug")


    

    




# heroku config:set DATABASE_URL=“postgres://<username>:<password>@<rds_writer_endpoint>:5432/<heroku_db_name>?sslmode=verify-full&sslrootcert=<location_of_cert>”

    # key = click.prompt(click.style("Please enter your Heroku API key", fg = 'green'))

    # appName = click.prompt(click.style("Please enter your app name", fg = 'green'))

    # heroku_conn = heroku3.from_key(key)
    # except requests.exceptions.HTTPError as err:
    #     click.echo("Oops...")
    #     quit()

    # try:
    #     app = heroku_conn.apps()[appName]
    # except requests.exceptions.HTTPError as err:
    #     click.secho("No app with that name and API key", fg = 'green')
    #     quit()

    # # account = heroku_conn.account()
    # # click.echo(app)
    # # click.echo(account)
    # click.secho("Your app's features:", fg = 'green')
    # click.echo(app.features())

    # addonlist = app.addons(order_by='id')
    # if len(addonlist) == 0:
    #     click.secho("No add-ons", fg = 'green')
    # else:
    #     click.secho("Your app's add-ons:", fg = 'green')
    #     click.echo(addonlist)
    #     # MAP ADDONS TO AWS SERVICES
    
    # domainlist = app.domains(order_by='id')
    # click.secho("Your app's domain:", fg = 'green')
    # click.echo(domainlist)

    # dynolist = app.dynos()
    # click.secho("Your app's dynos:", fg = 'green')
    # click.echo(dynolist)

    # click.echo(app.config())

if __name__ == "__main__":
    main()

    