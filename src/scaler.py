# custom imports
from config import Config
from environment import Environment

# public imports
import os
from ghapi.all import GhApi
import boto3
import botocore.exceptions
import logging


class Scaler:
    def __init__(self):
        self.config_obj = Config()
        self.environment_obj = Environment()
        self.ec2 = boto3.resource(
            "ec2",
            aws_access_key_id=self.environment_obj.get_aws_access_key_id(),
            aws_secret_access_key=self.environment_obj.get_aws_secret_access_key(),
            region_name=self.config_obj.get_aws_region(),
        )
        self.ssm = boto3.client(
            "ssm",
            aws_access_key_id=self.environment_obj.get_aws_access_key_id(),
            aws_secret_access_key=self.environment_obj.get_aws_secret_access_key(),
            region_name=self.config_obj.get_aws_region(),
        )
        self.github_api_obj = GhApi(
            repo=self.environment_obj.get_github_repository(),
            owner=self.environment_obj.get_github_owner(),
            token=self.environment_obj.get_github_token(),
        )

    # create a github runner based on architecture "arm64" or "amd64"
    def create_github_runner_ec2(self, architecture):
        result = self.ec2.create_instances(
            LaunchTemplate={
                "LaunchTemplateId": self.config_obj.get_aws_launch_templates()
                .get(architecture)
                .get("id")
            },
            MaxCount=1,
            MinCount=1,
        )
        return result[0].id

    # create a github runner token
    def create_github_runner_token(self):
        logging.info("creating github runner token")
        response = self.github_api_obj.actions.create_registration_token_for_repo()
        logging.info("successfully created a github runner token")
        return response["token"]

    # store the github runner config (token, repository, owner) in ssm with runner_id
    def store_github_runner_config_ssm(self, key, value):
        try:
            logging.info(f"attempting to store data with key as {key}")
            result = self.ssm.put_parameter(Type="String", Name=key, Value=value)
            logging.info(f"successfully stored data in ssm {result}")
        except botocore.exceptions.ClientError as err:
            logging.error(f"failed to store data: {err}")
            raise err

    # cleanup the github runner config (token, repository, owner) in ssm with runner_id
    def cleanup_github_runner_config_ssm(self, key):
        try:
            logging.info(f"attempting to clean up key {key}")
            result = self.ssm.delete_parameter(Name=key)
            logging.info(f"successfully cleaned up key in ssm {result}")
        except botocore.exceptions.ClientError as err:
            logging.error(f"failed to clean up key: {err}")
            raise err

    # scale up
    def scale_up(self, architecture):
        token = self.create_github_runner_token()
        runner_id = self.create_github_runner_ec2(architecture=architecture)
        self.store_github_runner_config_ssm(
            key=runner_id + "_GITHUB_TOKEN", value=token
        )
        self.store_github_runner_config_ssm(
            key=runner_id + "_GITHUB_OWNER",
            value=self.environment_obj.get_github_owner(),
        )
        self.store_github_runner_config_ssm(
            key=runner_id + "_GITHUB_REPOSITORY",
            value=self.environment_obj.get_github_repository(),
        )

    # terminate a github runner using runner_id
    def terminate_github_runner_ec2(self, runner_id):
        try:
            logging.info(f"attempting to terminate ec2 instance with id {runner_id}")
            result = self.ec2.instances.filter(InstanceIds=[runner_id]).terminate()
            logging.info(f"successfully terminated instance {runner_id} : {result}")
        except Exception as err:
            logging.info(f"failed to terminate instance: {err}")
            raise err

    def deregister_github_runner_from_repo(self, runner_id):
        logging.info(f"attempting to deregister github runner {runner_id}")
        found = False
        result = self.github_api_obj.actions.list_self_hosted_runners_for_repo()
        for runner in result["runners"]:
            if runner["name"] == runner_id:
                found = True
                self.github_api_obj.actions.delete_self_hosted_runner_from_repo(
                    runner["id"]
                )
                logging.info(f"successfully deregistered github runner {runner_id}")
        if not found:
            # ideally we should not reach this state
            logging.info(f"runner {runner_id} not found")

    def get_active_runners(self):
        logging.info("fetching active runners")
        result = self.github_api_obj.actions.list_self_hosted_runners_for_repo()
        active_runners = []
        for runner in result["runners"]:
            if runner["status"] == "online":
                active_runners.append(runner)
        logging.info(f"current active runners: {active_runners}")
        return active_runners

    def get_idle_runners(self):
        logging.info("fetching idle runners")
        result = self.github_api_obj.actions.list_self_hosted_runners_for_repo()
        idle_runners = []
        for runner in result["runners"]:
            if runner["busy"] is False:
                idle_runners.append(runner)
        logging.info(f"current idle runners: {idle_runners}")
        return idle_runners

    def get_queued_workflow_runs(self):
        logging.info("fetching queued workflow runs")
        result = self.github_api_obj.actions.list_workflow_runs_for_repo()
        queued_workflow_runs = []
        for workflow_run in result["workflow_runs"]:
            if workflow_run["status"] == "queued":
                queued_workflow_runs.append(workflow_run)
        logging.info(f"queued workflow runs: {queued_workflow_runs}")
        return queued_workflow_runs

    # scale down
    def scale_down(self, runner_id):
        self.cleanup_github_runner_config_ssm(key=runner_id + "_GITHUB_TOKEN")
        self.cleanup_github_runner_config_ssm(key=runner_id + "_GITHUB_OWNER")
        self.cleanup_github_runner_config_ssm(key=runner_id + "_GITHUB_REPOSITORY")
        self.terminate_github_runner_ec2(runner_id=runner_id)
        self.deregister_github_runner_from_repo(runner_id=runner_id)

