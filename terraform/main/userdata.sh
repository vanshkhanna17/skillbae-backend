#!/bin/bash

apt update -y

apt install -y docker.io git

systemctl enable docker
systemctl start docker

curl -SL https://github.com/docker/compose/releases/download/v5.1.3/docker-compose-linux-aarch64 \
-o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose