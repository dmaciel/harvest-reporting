import logging
import sys

from hreporting import config
from hreporting.harvest_client import HarvestClient
from hreporting.notifications import NotificationManager
from hreporting.utils import load_yaml, load_yaml_file, read_cloud_storage

logging.getLogger("harvest_reports")
logging.basicConfig(format="%(asctime)s %(message)s")
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def client_is_filtered(client, filter_list=None):
    if not filter_list:
        return client["is_active"]

    return client["is_active"] and client["name"] in filter_list


def main_method(
    bearer_token, harvest_account, global_config, from_email, exception_hooks=None
):
    harvest_client = HarvestClient(bearer_token, harvest_account, global_config)
    client_filter = global_config.get("client_filter", [])

    active_clients = [
        client
        for client in harvest_client.list_clients()
        if client_is_filtered(client, filter_list=client_filter)
    ]

    notifications = NotificationManager(
        clients=active_clients,
        fromEmail=from_email,
        exceptionHooks=global_config.get("exceptionHook"),
        emailTemplateId=global_config.get("emailTemplateId", None),
        harvestClient=harvest_client,
    )

    notifications.send()

    notifications.send_completion(
        verification_hook=global_config.get("sendVerificationHook"),
        clients=active_clients,
    )


def harvest_reports(*args):
    bearer_token = config.BEARER_TOKEN
    bucket = config.BUCKET
    config_path = config.CONFIG_PATH
    harvest_account = config.HARVEST_ACCOUNT
    from_email = config.ORIGIN_EMAIL_ADDRESS

    global_config = (
        load_yaml_file(config_path)
        if not bucket
        else load_yaml(read_cloud_storage(bucket, config_path))
    )

    return main_method(
        bearer_token=bearer_token,
        harvest_account=harvest_account,
        global_config=global_config,
        from_email=from_email,
    )


if __name__ == "__main__":
    harvest_reports()
