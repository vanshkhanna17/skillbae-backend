#!/bin/bash

set -e

dnf update -y

dnf install -y \
  docker \
  git \
  awscli

systemctl enable docker

systemctl start docker

usermod -aG docker ec2-user

mkdir -p /usr/local/lib/docker/cli-plugins

curl -SL \
https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-linux-x86_64 \
-o /usr/local/lib/docker/cli-plugins/docker-compose

chmod +x \
/usr/local/lib/docker/cli-plugins/docker-compose

docker --version

docker compose version

aws --version