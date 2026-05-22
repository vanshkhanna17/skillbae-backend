#!/bin/bash

set -e

apt update -y

apt install -y docker.io git awscli

systemctl enable docker
systemctl start docker

curl -SL https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-linux-x86_64 \
-o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose

usermod -aG docker ubuntu