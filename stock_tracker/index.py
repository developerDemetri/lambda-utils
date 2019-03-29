import logging
import os
import re
import requests

IS_DEBUGGING = "debugging" in os.environ and os.environ["debugging"] == "yes"
AV_API_KEY = str(os.environ.get("ALPHA_VANTAGE_KEY", "demo")).strip()
AV_URI = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={}&apikey={}"
TICKER_RE = re.compile("^[A-Z]{1,5}$")

logging.basicConfig(level=logging.DEBUG if IS_DEBUGGING else logging.INFO,
                    format="%(asctime)s %(levelname)-8s %(message)s")
LOGGER = logging.getLogger()
LOGGER.debug("Loading lambda...")


def stock_tracker_handler(event, context):
    LOGGER.info("Running stock tracker...")
    stock_symbol = str(event["symbol"]).strip().upper()
    if TICKER_RE.fullmatch(stock_symbol) is None:
        err_msg = "Invalid stock ticker: {}!".format(stock_symbol)
        LOGGER.error(err_msg)
        raise ValueError(err_msg)

    LOGGER.debug("Retrieving stock info from Alphavantage for {}...".format(stock_symbol))
    final_uri = AV_URI.format(stock_symbol, AV_API_KEY)
    LOGGER.debug("Calling {}...".format(final_uri))
    stock_req = requests.get(final_uri)
    if not stock_req.ok:
        LOGGER.error("Alphavantage request failed with status: {}!".format(stock_req.status_code))
        stock_req.raise_for_status()
    LOGGER.info("Successfully retrieved stock info from Alphavantage for {}.".format(stock_symbol))

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

    result = "{}: {:.2f} {}{:.2f} ({}{:.2f}%)".format(stock_symbol, stock_price,
                                                      stock_change_symbol, abs(stock_change),
                                                      stock_change_symbol, stock_change_percent)
    LOGGER.info(result)
    return result
