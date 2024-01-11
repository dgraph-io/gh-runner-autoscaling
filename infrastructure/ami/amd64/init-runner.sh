#!/bin/bash
# Sleep 30secs on boot
sleep 30
# Get GH Actions Runner registration token
export AWS_REGION=us-east-1
AWS_INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
AWS_INSTANCE_ID_GITHUB_TOKEN=$(echo $AWS_INSTANCE_ID)_GITHUB_TOKEN
AWS_INSTANCE_ID_GITHUB_OWNER=$(echo $AWS_INSTANCE_ID)_GITHUB_OWNER
AWS_INSTANCE_ID_GITHUB_REPOSITORY=$(echo $AWS_INSTANCE_ID)_GITHUB_REPOSITORY
GITHUB_TOKEN=$(aws ssm get-parameter --name $AWS_INSTANCE_ID_GITHUB_TOKEN --region $AWS_REGION | jq -r '.Parameter.Value')
GITHUB_OWNER=$(aws ssm get-parameter --name $AWS_INSTANCE_ID_GITHUB_OWNER --region $AWS_REGION | jq -r '.Parameter.Value')
GITHUB_REPOSITORY=$(aws ssm get-parameter --name $AWS_INSTANCE_ID_GITHUB_REPOSITORY --region $AWS_REGION | jq -r '.Parameter.Value')
sudo -i -u ubuntu bash << EOF
# Install & Setup GH Actions Runner
cd /home/ubuntu
mkdir actions-runner && cd actions-runner
if [ "$(uname -m)" = "aarch64" ]; then
    echo "Detected arm64 architecture"
    # Download the latest runner package
    curl -o actions-runner-linux-arm64-2.298.2.tar.gz -L https://github.com/actions/runner/releases/download/v2.298.2/actions-runner-linux-arm64-2.298.2.tar.gz
    # Optional: Validate the hash
    echo "803e4aba36484ef4f126df184220946bc151ae1bbaf2b606b6e2f2280f5042e8  actions-runner-linux-arm64-2.298.2.tar.gz" | shasum -a 256 -c
    # Extract the installer
    tar xzf ./actions-runner-linux-arm64-2.298.2.tar.gz
elif [ "$(uname -m)" = "x86_64" ]; then
    echo "Detected amd64 architecture"
    # Download the latest runner package
    curl -o actions-runner-linux-x64-2.298.2.tar.gz -L https://github.com/actions/runner/releases/download/v2.298.2/actions-runner-linux-x64-2.298.2.tar.gz
    # Optional: Validate the hash
    echo "0bfd792196ce0ec6f1c65d2a9ad00215b2926ef2c416b8d97615265194477117  actions-runner-linux-x64-2.298.2.tar.gz" | shasum -a 256 -c
    # Extract the installer
    tar xzf ./actions-runner-linux-x64-2.298.2.tar.gz
else
    echo "Unrecognized architecture"
    exit 1
fi
# Create the runner and start the configuration experience
./config.sh --unattended --url https://github.com/$GITHUB_OWNER/$GITHUB_REPOSITORY --token $GITHUB_TOKEN --name $AWS_INSTANCE_ID
# Delete AWS SSM Token
aws ssm delete-parameter --name $AWS_INSTANCE_ID_GITHUB_TOKEN --region $AWS_REGION
aws ssm delete-parameter --name $AWS_INSTANCE_ID_GITHUB_OWNER --region $AWS_REGION
aws ssm delete-parameter --name $AWS_INSTANCE_ID_GITHUB_REPOSITORY --region $AWS_REGION
# Start GH Actions
sudo ./svc.sh install
sudo ./svc.sh start
# Reboot Machine
sudo reboot
EOF
