import logging
import sys

import yaml
from google.cloud import storage
from taosdevopsutils.slack import Slack

# In the future if we need to auth with multiple workspaces we might need
# to move this to a factory method and pull a specific client for each token
SLACK_CLIENT = Slack()

logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(message)s")

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def print_verify(used, client_name, percent, left) -> None:
    """ Print Details for verification """

    hour_report_template = """
    Client:           {name}
    Used Hours:       {used}
    Remaining Hours:  {left}
    Color:            {color}
    Percent:          {percent}
    """
    logging.info(
        str.format(
            hour_report_template,
            name=client_name,
            used=used,
            left=left,
            percent="%d%%" % (percent),
            color=get_color_code_for_utilization(percent),
        )
    )


# Define decimal place to truncate
def truncate(n, decimals=0) -> float:
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


def load_yaml_file(file_handle):
    return yaml.load(open(file_handle), Loader=yaml.Loader)


def load_yaml(yaml_string):
    return yaml.load(yaml_string, Loader=yaml.Loader)


def get_color_code_for_utilization(percent) -> str:
    blue = "#0000ff"
    green = "#33cc00"
    yellow = "#ffcc00"
    orange = "#ff6600"
    red = "#ff0000"

    if percent < 40:
        return blue

    if percent < 65:
        return green

    if percent < 87:
        return yellow

    if percent < 95:
        return orange

    return red


# Define types of payloads
def get_payload(used, client_name, percent, left, _format="slack") -> dict:
    """ Get payload for every type of format"""
    try:

        return {"slack": get_slack_payload, "teams": get_teams_payload}[_format](
            used, client_name, percent, left
        )

    except KeyError:
        raise Exception(f"Invalid Payload format {_format}")


def get_slack_payload(used, client_name, percent, left, *args) -> dict:
    """ Format JSON body for Slack channel posting"""

    return {
        "attachments": [
            {
                "color": get_color_code_for_utilization(percent),
                "title": client_name,
                "text": "%d%%" % (percent),
                "fields": [
                    {"title": "Hours Used", "value": used, "short": "true"},
                    {"title": "Hours Remaining", "value": left, "short": "true"},
                ],
            }
        ]
    }


def get_teams_payload(used, client_name, percent, left, *args) -> dict:
    """ Format JSON body for MS Teams channel post"""

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": get_color_code_for_utilization(percent),
        "title": "DevOps Time Reports",
        "text": client_name,
        "sections": [
            {"text": "%d%%" % (percent)},
            {"activityTitle": "Hours Used", "activitySubtitle": used},
            {"activityTitle": "Hours Remaining", "activitySubtitle": left},
        ],
    }


# Post to channel/workspace
def channel_post(webhook_url: str, used, client_name, percent, left) -> dict:
    """ Posts payload to webhook provided """
    post_format = (
        "teams" if webhook_url.startswith("https://outlook.office.com") else "slack"
    )

    data = get_payload(used, client_name, percent, left, _format=post_format)
    response = SLACK_CLIENT.post_slack_message(webhook_url, data)
    logging.info(response)

    return response


def read_cloud_storage(bucket_name, file_name) -> str:
    """ Returns file contents from provided bucket and file names """
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(file_name)
    response = blob.download_as_string()

    return response


def exception_channel_post(exception, client, webhook_url) -> dict:
    """
    Performs a protected attempt to send slack message about an error.
    Wraps try blocks for assurance that the message will not further break the system.
    """

    data = {
        "attachments": [
            {
                "color": "#ff0000",
                "title": f"Exception while processing {client['name']}",
                "text": str(exception),
            }
        ]
    }

    response = SLACK_CLIENT.post_slack_message(webhook_url, data)
    logging.error(response)

    return response
