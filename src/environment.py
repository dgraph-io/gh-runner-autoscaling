import os


class Environment:
    def __init__(self):
        pass

    @staticmethod
    def get(environment_key, default_value=None):
        if default_value == "" or default_value is None:
            try:
                return os.environ[environment_key]
            except KeyError:
                raise Exception(f"{environment_key} does not exist")
        else:
            return os.getenv(environment_key, default_value)

    def get_github_owner(self):
        return self.get("GH_OWNER")

    def get_github_repository(self):
        return self.get("GH_REPOSITORY")

    def get_github_token(self):
        return self.get("GH_TOKEN")

    def get_aws_access_key_id(self):
        return self.get("AWS_ACCESS_KEY_ID")

    def get_aws_secret_access_key(self):
        return self.get("AWS_SECRET_ACCESS_KEY")
