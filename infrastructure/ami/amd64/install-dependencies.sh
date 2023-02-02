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
# CI Permission Issue
sudo touch /etc/cron.d/ci_permissions_resetter
sudo chown $USER:$USER /etc/cron.d/ci_permissions_resetter
sudo echo "* * * * * root for i in {0..60}; do chown -R $USER:$USER /home/ubuntu/actions-runner/_work & sleep 1; done" >  /etc/cron.d/ci_permissions_resetter
sudo chown root:root /etc/cron.d/ci_permissions_resetter
# Increase file descriptor limit
sudo sh -c 'echo "*         hard    nofile      2000000" >> /etc/security/limits.conf'
sudo sh -c 'echo "*         soft    nofile      2000000" >> /etc/security/limits.conf'
sudo sh -c 'echo "root      hard    nofile      2000000" >> /etc/security/limits.conf'
sudo sh -c 'echo "root      soft    nofile      2000000" >> /etc/security/limits.conf'
sudo sh -c 'echo "fs.nr_open = 2000000" >> /etc/sysctl.conf'
# AWS CLI Setup
sudo apt-get install -y awscli
