#!/bin/bash

set -e

dnf update -y

dnf install -y \
  docker \
  git \
  awscli \
  amazon-ssm-agent

systemctl enable docker
systemctl start docker

# SSM agent — required for GitHub Actions to deploy via ssm send-command
# without opening port 22 to the internet
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Create the app directory — deploy script writes .env here and runs docker compose
# The actual app code lives in the ECR image, no repo clone needed
mkdir -p /home/ec2-user/skillbae-backend
chown ec2-user:ec2-user /home/ec2-user/skillbae-backend

# Install Docker Compose plugin — detect arch so it works on both x86_64 and arm64
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
  COMPOSE_ARCH="aarch64"
else
  COMPOSE_ARCH="x86_64"
fi

curl -SL "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-linux-${COMPOSE_ARCH}" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

usermod -aG docker ec2-user

mkdir -p /usr/local/lib/docker/cli-plugins

curl -SL \
https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-linux-aarch64 \
-o /usr/local/lib/docker/cli-plugins/docker-compose

chmod +x \
/usr/local/lib/docker/cli-plugins/docker-compose

docker --version

docker compose version

aws --version