#!/bin/bash
# Machine Setup
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install \
    dialog \
    apt-utils \
    ca-certificates \
    curl \
    unzip \
    jq \
    gnupg \
    nfs-kernel-server \
    lsb-release \
    build-essential #Libc Packages
# Docker Setup
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
 echo \
   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get -y update
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo apt-get -y install docker-compose
#Add Docker to sudoers group
sudo usermod -aG docker ${USER}
newgrp docker &
# AWS CLI Setup
sudo apt-get install -y awscli
