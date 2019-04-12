from datetime import datetime
import logging
import os

import boto3
from pytz import timezone
import requests
from requests.exceptions import ReadTimeout

IS_DEBUGGING = str(os.environ.get("DEBUGGING", "no")).strip().lower() == "yes"
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG if IS_DEBUGGING else logging.INFO)
LOGGER.debug("Loading lambda...")

AWS_REGION = str(os.environ.get("AWS_REGION", "us-west-2")).strip()
MAX_TIME = 3
SITES_PARAM = str(os.environ.get("SITES_PARAM", "/Demo/Sites")).strip()
STATS_DYNAMO_TABLE = str(os.environ.get("STATS_DYNAMO_TABLE", "demo")).strip()
TIMEZONE = str(os.environ.get("TIMEZONE", "US/Pacific")).strip()


def get_sites():
    LOGGER.info("Retrieving list of sites...")
    ssm_client = boto3.client("ssm", region_name=AWS_REGION)
    sites = list()
    for site in ssm_client.get_parameter(Name=SITES_PARAM)["Parameter"]["Value"].split(","):
        sites.append(site.strip().lower())
    return sites


def save_stats(sites):
    LOGGER.info("Saving all Site info in Dynamo...")
    dynamo_client = boto3.client("dynamodb", region_name=AWS_REGION)
    for site in sites:
        dynamo_client.put_item(
            TableName=STATS_DYNAMO_TABLE,
            Item={
                "name": {"S": site["name"]},
                "timestamp": {"S": site["check_time"]},
                "is_down": {"BOOL": site["is_down"]},
                "response_code": {"N": str(site["response_code"])},
                "response_time": {"N": str(site["response_time"])}
            }
        )
        LOGGER.debug("Successfully updated Stats table for {}.".format(site["name"]))
    LOGGER.info("Successfully saved all Site info in Dynamo.")


def site_monitor_handler(event, context):
    LOGGER.debug("Running site monitor...")
    sites = get_sites()
    results = list()
    for site in sites:
        site_results = dict({"name": site})
        site_results["check_time"] = datetime.now(timezone(TIMEZONE)).isoformat()
        try:
            resp = requests.get("https://{}".format(site), timeout=MAX_TIME)
            site_results["is_down"] = bool(resp.status_code != 200)
            site_results["response_code"] = int(resp.status_code)
            site_results["response_time"] = float(resp.elapsed.total_seconds())
        except ReadTimeout as err:
            LOGGER.warning("Site check {} timed out: {}".format(site, err))
            site_results["is_down"] = True
            site_results["response_code"] = 504
            site_results["response_time"] = MAX_TIME
        LOGGER.debug(site_results)
        results.append(site_results)
    save_stats(results)
    LOGGER.info("Successfully ran site monitor.")
