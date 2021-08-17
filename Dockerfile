FROM python:3.8-slim
RUN useradd --create-home --shell /bin/bash app_user
RUN pip install click
RUN apt-get -y update && apt-get -y install curl && apt-get install -y git && apt-get -y install sudo
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN curl https://cli-assets.heroku.com/install.sh | sh
ENV NODE_VERSION=12.6.0
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version
RUN npm install aws-cdk
RUN pip3 install aws-cdk.aws-rds
RUN pip3 install aws-cdk.aws-apprunner
RUN pip3 install aws-cdk.aws-elasticbeanstalk
RUN pip3 --no-cache-dir install --upgrade awscli
RUN pip3 install requests
RUN pip3 install heroku3
USER app_user
COPY . .
CMD ["bash"]
CMD [ "python", "hello_cdk/discover_heroku.py"]
