import yaml
import os


class Config:
    def __init__(
        self,
        yaml_file_path=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.yaml"
        ),
    ):
        yaml_content = open(yaml_file_path).read()
        self.yaml_data = yaml.safe_load(yaml_content)

    def get_aws(self):
        return self.yaml_data["aws"]

    def get_aws_launch_templates(self):
        return self.get_aws()["launch_templates"]

    def get_aws_launch_templates_amd64(self):
        return self.get_aws_launch_templates()["amd64"]

    def get_aws_launch_templates_amd64_id(self):
        return self.get_aws_launch_templates_amd64()["id"]

    def get_aws_launch_templates_amd64_name(self):
        return self.get_aws_launch_templates_amd64()["name"]

    def get_aws_launch_templates_arm64(self):
        return self.get_aws_launch_templates()["arm64"]

    def get_aws_launch_templates_arm64_id(self):
        return self.get_aws_launch_templates_arm64()["id"]

    def get_aws_launch_templates_arm64_name(self):
        return self.get_aws_launch_templates_arm64()["name"]

    def get_aws_region(self):
        return self.get_aws()["region"]

    def get_github_repositories(self):
        return self.yaml_data["github_repositories"]

    def get_orchestrator(self):
        return self.yaml_data["orchestrator"]

    def get_orchestrator_github_ratelimit_timewait_seconds(self):
        return self.get_orchestrator()["GITHUB_RATELIMIT_TIMEWAIT_SECONDS"]

    def get_orchestrator_aws_ratelimit_timewait_seconds(self):
        return self.get_orchestrator()["AWS_RATELIMIT_TIMEWAIT_SECONDS"]

    def get_orchestrator_github_runner_timeout_seconds(self):
        return self.get_orchestrator()["GITHUB_RUNNER_TIMEOUT_SECONDS"]
