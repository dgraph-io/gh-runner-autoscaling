# public imports
import argparse
import os
import time
import logging
from datetime import datetime
from datetime import timedelta

# custom imports
from scaler import Scaler
from config import Config


def scale_up_fn():
    scaler_obj = Scaler()
    scaler_obj.scale_up(architecture=args.architecture)


def scale_down_fn():
    scaler_obj = Scaler()
    scaler_obj.scale_down(runner_id=args.runner_id)


def auto_scaling_fn():
    config_obj = Config()
    github_repositories = config_obj.get_github_repositories()
    start_time = datetime.now()
    i = 0
    while True:
        current_time = datetime.now()
        if current_time < start_time + timedelta(
            seconds=config_obj.get_orchestrator_github_runner_timeout_seconds()
        ):
            try:
                logging.info(f"****** run number {i}")
                for github_repository in github_repositories:
                    os.environ["GH_REPOSITORY"] = github_repository["GITHUB_REPOSITORY"]
                    os.environ["GH_OWNER"] = github_repository["GITHUB_OWNER"]
                    scaler_obj = Scaler()
                    queued_workflow_runs = scaler_obj.get_queued_workflow_runs()
                    idle_runners = scaler_obj.get_idle_runners()
                    if len(queued_workflow_runs) == 0 and len(idle_runners) == 0:
                        logging.info("no operation will be performed")
                        pass
                    elif len(queued_workflow_runs) == 0 and len(idle_runners) > 0:
                        logging.info("scale-down operation selected")
                        # scale-down idle runners
                        for idle_runner in idle_runners:
                            scaler_obj.scale_down(runner_id=idle_runner["name"])
                    elif len(queued_workflow_runs) > 0 and len(idle_runners) == 0:
                        logging.info("scale-up operation selected")
                        # scale-up runners
                        queued_workflow_runs_count = len(queued_workflow_runs) - 1
                        j = queued_workflow_runs_count
                        while j >= 0:
                            # TODO: we need to find a way to extract the labels
                            workflow_name = (
                                scaler_obj.github_api_obj.actions.get_workflow(
                                    workflow_id=queued_workflow_runs[j]["workflow_id"]
                                )["name"]
                            )
                            if (
                                workflow_name
                                in github_repository["SELF_HOSTED_WORKFLOWS_ARM64"]
                            ):
                                scaler_obj.scale_up(architecture="arm64")
                            if (
                                workflow_name
                                in github_repository["SELF_HOSTED_WORKFLOWS_AMD64"]
                            ):
                                scaler_obj.scale_up(architecture="amd64")
                            time.sleep(
                                config_obj.get_orchestrator_aws_ratelimit_timewait_seconds()
                            )
                            j = j - 1
                    elif len(queued_workflow_runs) > 0 and len(idle_runners) > 0:
                        diff = len(queued_workflow_runs) - len(idle_runners)
                        if diff == 0:
                            logging.info("no operation will be performed")
                            pass
                        elif diff > 0:
                            logging.info("partial scale-up operation selected")
                            # scale-up runners
                            j = diff
                            while j >= 0:
                                # TODO: we need to find a way to extract the labels
                                workflow_name = (
                                    scaler_obj.github_api_obj.actions.get_workflow(
                                        workflow_id=queued_workflow_runs[j][
                                            "workflow_id"
                                        ]
                                    )["name"]
                                )
                                if (
                                    workflow_name
                                    in github_repository["SELF_HOSTED_WORKFLOWS_ARM64"]
                                ):
                                    scaler_obj.scale_up(architecture="arm64")
                                if (
                                    workflow_name
                                    in github_repository["SELF_HOSTED_WORKFLOWS_AMD64"]
                                ):
                                    scaler_obj.scale_up(architecture="amd64")
                                time.sleep(
                                    config_obj.get_orchestrator_aws_ratelimit_timewait_seconds()
                                )
                                j = j - 1
                        elif diff < 0:
                            logging.info("partial scale-down operation selected")
                            # scale-down idle runners
                            for count, idle_runner in enumerate(idle_runners):
                                if count == abs(diff) - 1:
                                    break
                                else:
                                    scaler_obj.scale_down(runner_id=idle_runner["name"])
                        else:
                            pass
                    else:
                        pass
                time.sleep(
                    config_obj.get_orchestrator_github_ratelimit_timewait_seconds()
                )
            except Exception as e:
                logging.exception(e)
        else:
            logging.info(
                f"the auto functionality is gracefully terminating because of max GITHUB_RUNNER_TIMEOUT_SECONDS {config_obj.get_orchestrator_github_runner_timeout_seconds()}"
            )
            break
        i = i + 1


def setup_logging():
    log_format = (
        "[%(asctime)s] %(process)d {%(filename)s:%(lineno)d} %(funcName)s %(message)s"
    )
    logging.getLogger("").setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger("").addHandler(console)

    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scale.log")
    fh = logging.FileHandler(log_file)
    fh.setFormatter(logging.Formatter(log_format))
    logging.getLogger("").addHandler(fh)
    logging.info(f"Log file output set to {log_file}")


if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="github runner autoscaling")
    subparsers = parser.add_subparsers()

    scale_up = subparsers.add_parser("up", description="scale up runners")
    scale_up.add_argument(
        "-a",
        "--architecture",
        required=True,
        help="architecture arm64 or amd64",
        choices=["arm64", "amd64"],
    )
    scale_up.set_defaults(func=scale_up_fn)

    scale_down = subparsers.add_parser("down", description="scale down runners")
    scale_down.add_argument("-r", "--runner_id", required=True, help="runner_id")
    scale_down.set_defaults(func=scale_down_fn)

    auto_scaling = subparsers.add_parser("auto", description="auto scaling runners")
    auto_scaling.set_defaults(func=auto_scaling_fn)

    args = parser.parse_args()
    args.func()
