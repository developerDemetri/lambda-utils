from datetime import datetime
import logging
import os

import boto3
import requests

IS_DEBUGGING = str(os.environ.get("DEBUGGING", "no")).strip().lower() == "yes"
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG if IS_DEBUGGING else logging.INFO)
LOGGER.debug("Loading lambda...")

AWS_REGION = str(os.environ.get("AWS_REGION", "us-west-2")).strip()
SITE_DYNAMO_TABLE = str(os.environ.get("SITE_DYNAMO_TABLE", "demo")).strip()
STATS_DYNAMO_TABLE = str(os.environ.get("STATS_DYNAMO_TABLE", "demo")).strip()
SNS_TOPIC = str(os.environ.get("SNS_TOPIC", "demo")).strip()


def get_sites(dynamo_client):
    LOGGER.info("Retrieving list of sites...")
    sites = []
    for item in dynamo_client.scan(TableName=SITE_DYNAMO_TABLE, ConsistentRead=True)["Items"]:
        sites.append({
            "id": int(item["site_id"]["N"]),
            "name": str(item["site_name"]["S"]),
            "is_down": bool(item["is_down"]["BOOL"])
        })
    LOGGER.debug(str(sites))
    LOGGER.info("Successfully retrieved list of {} sites.".format(len(sites)))
    return sites

def save_stats(dynamo_client, sites):
    LOGGER.info("Saving all Site info in Dynamo...")
    for site in sites:
        LOGGER.info("Saving info in Dynamo for {}...".format(site["name"]))
        dynamo_client.update_item(
            TableName=SITE_DYNAMO_TABLE,
            Key={"site_id": {"N": str(site["id"])}},
            UpdateExpression="SET is_down = :val",
            ExpressionAttributeValues={":val": {"BOOL": site["is_down"]}}
        )
        LOGGER.debug("Successfully updated Site table for {}.".format(site["name"]))

        dynamo_client.put_item(
            TableName=STATS_DYNAMO_TABLE,
            Item={
                "site_id": {"N": str(site["id"])},
                "site_name": {"S": site["name"]},
                "timestamp": {"S": site["check_time"]},
                "is_down": {"BOOL": site["is_down"]},
                "response_code": {"N": str(site["response_code"])},
                "response_time": {"N": str(site["response_time"])}
            }
        )
        LOGGER.debug("Successfully updated Stats table for {}.".format(site["name"]))
    LOGGER.info("Successfully saved all Site info in Dynamo.")

def send_alert(sns_client, account_id, down_site_list):
    if down_site_list:
        LOGGER.debug("Down Site List: {}".format(down_site_list))
        LOGGER.warning("Alerting for {} site(s) down...".format(len(down_site_list)))
        message_parts = ["The following site(s) returned unhealthy responses:"]
        for site_info in down_site_list:
            message_parts.append("\t{}\t{}".format(site_info["name"], site_info["response_code"]))
        message_parts.append("DeveloperDemetri Site Monitor")
        LOGGER.debug("\n".join(message_parts))

        sns_client.publish(
            TopicArn="arn:aws:sns:{}:{}:{}".format(AWS_REGION, account_id, SNS_TOPIC),
            Subject="Site Monitor Alert: Webite(s) Down",
            Message="\n".join(message_parts)
        )
        LOGGER.info("Sucessfully alerted for {} site(s) down...".format(len(down_site_list)))
    else:
        LOGGER.info("No Sites to alert on :)")

def site_monitor_handler(event, context):
    LOGGER.debug("Running site monitor...")
    dynamo_client = boto3.client("dynamodb")
    sns_client = boto3.client("sns")

    crashed_sites = []
    sites = get_sites(dynamo_client)
    for site in sites:
        already_down = site["is_down"]
        site["check_time"] = datetime.now().isoformat()
        resp = requests.get("https://{}".format(site["name"]))
        site["is_down"] = bool(resp.status_code != 200)
        site["response_code"] = int(resp.status_code)
        site["response_time"] = float(resp.elapsed.total_seconds())
        LOGGER.debug(str(site))

        if site["is_down"] and not already_down:
            crashed_sites.append(site)

    account_id = context.invoked_function_arn.split(":")[4]
    save_stats(dynamo_client, sites)
    send_alert(sns_client, account_id, crashed_sites)
    LOGGER.info("Successfully ran site monitor.")
