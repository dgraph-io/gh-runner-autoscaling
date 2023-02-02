packer {
  required_plugins {
    amazon = {
      version = ">= 0.0.2"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "instance_type" {
  type        = string
  default     = "a1.4xlarge"
  description = "Instance type to use for creating the image"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  type    = string
  default = "staging"
}

source "amazon-ebs" "ubuntu" {
  ami_name      = "gh-runner-linux-arm64-aws"
  profile       = var.aws_profile
  instance_type = var.instance_type
  region        = var.region
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/*ubuntu-focal-20.04-arm64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]
  }
  ssh_username = "ubuntu"
}

build {
  name = "gh-runner"
  sources = [
    "source.amazon-ebs.ubuntu"
  ]
  provisioner "shell" {
    inline = ["sleep 10"]
  }
  provisioner "shell" {
    script = "install-dependencies.sh"
  }
  provisioner "file" {
    source      = "init-runner.sh"
    destination = "/tmp/init-runner.sh"
  }
  provisioner "shell" {
    inline = [
      # A hack to make cloud-init run the script when a new instance is first booted
      # Ref: https://cloudinit.readthedocs.io/en/latest/topics/modules.html?highlight=per%20instance#scripts-per-instance
      "sudo mv /tmp/init-runner.sh /var/lib/cloud/scripts/per-instance/init-runner.sh",
      "sudo chmod 744 /var/lib/cloud/scripts/per-instance/init-runner.sh"
    ]
  }
}
