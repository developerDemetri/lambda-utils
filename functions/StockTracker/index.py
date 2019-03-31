import logging
import os
import re

import boto3
import requests

IS_DEBUGGING = str(os.environ.get("DEBUGGING", "no")).strip().lower() == "yes"
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG if IS_DEBUGGING else logging.INFO)
LOGGER.debug("Loading lambda...")

AWS_REGION = str(os.environ.get("AWS_REGION", "us-west-2")).strip()
AV_API_KEY = str(os.environ.get("ALPHA_VANTAGE_KEY", "demo")).strip()
AV_URI = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}"
SNS_TOPIC = str(os.environ.get("SNS_TOPIC", "demo")).strip()
SYMBOLS_PARAM = str(os.environ.get("SYMBOLS_PARAM", "/Demo/Symbols")).strip()
TICKER_RE = re.compile("^[A-Z]{1,5}$")


def get_stock_symbols():
    ssm_client = boto3.client("ssm", region_name=AWS_REGION)
    symbols = []
    for symbol in ssm_client.get_parameter(Name=SYMBOLS_PARAM)["Parameter"]["Value"].split(","):
        symbols.append(symbol.strip().upper())
    return symbols

def send_results(results, account_id):
    if results:
        LOGGER.info("Sending results to SNS Topic: {}...")
        sns_client = boto3.client("sns")
        sns_client.publish(
            TopicArn="arn:aws:sns:{}:{}:{}".format(AWS_REGION, account_id, SNS_TOPIC),
            Message="\n{}".format("\n".join(results))
        )
        LOGGER.info("Successfully sent results to SNS Topic: {}.")
    else:
        LOGGER.warning("No results to send!")

def stock_tracker_handler(event, context):
    LOGGER.info("Running stock tracker...")
    if "symbol" in event:
        stock_symbols = [str(event["symbol"]).strip().upper()]
    else:
        stock_symbols = get_stock_symbols()

    results = []
    for stock_symbol in stock_symbols:
        if TICKER_RE.fullmatch(stock_symbol) is None:
            err_msg = "Invalid stock ticker: {}!".format(stock_symbol)
            LOGGER.error(err_msg)
            raise ValueError(err_msg)

        LOGGER.debug("Retrieving stock info from Alphavantage for {}...".format(stock_symbol))
        final_uri = AV_URI.format(stock_symbol, AV_API_KEY)
        LOGGER.debug("Calling {}...".format(final_uri))
        stock_req = requests.get(final_uri)
        if not stock_req.ok:
            LOGGER.error("Alphavantage request failed with status: {}!"
                         .format(stock_req.status_code))
            stock_req.raise_for_status()
        LOGGER.info("Successfully retrieved stock info from Alphavantage for {}."
                    .format(stock_symbol))

        LOGGER.debug("Parsing lastest stock info for {}...".format(stock_symbol))
        stock_info = stock_req.json()["Global Quote"]
        if stock_info is None or not bool(stock_info):
            err_msg = "Alphavantage returned empty response!"
            LOGGER.error(err_msg)
            raise ValueError(err_msg)
        stock_price = float(stock_info["05. price"])
        stock_change = float(stock_info["09. change"])
        stock_change_symbol = "-" if stock_change < 0 else "+"
        stock_change_percent = abs(float(stock_info["10. change percent"].rstrip("%")))
        LOGGER.debug("Successfully parsed lastest stock info for {}.".format(stock_symbol))

        result = "{}: ${:.2f} {}${:.2f} ({}{:.2f}%)".format(stock_symbol,
                                                            stock_price,
                                                            stock_change_symbol,
                                                            abs(stock_change),
                                                            stock_change_symbol,
                                                            stock_change_percent)
        LOGGER.info(result)
        results.append(result)

    account_id = context.invoked_function_arn.split(":")[4]
    send_results(results, account_id)

    return results
