import boto3
from flexmock import flexmock
import pytest
import requests
from requests.exceptions import HTTPError

from src.StockTracker import index

FAKE_URI = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=GDDY&apikey=demo"
EXPECTED_RESULTS = ["GDDY: $75.11 +$0.90 (+1.21%)"]


def test_get_symbols():
    fake_client = flexmock()
    fake_client.should_receive("get_parameter").with_args(Name="/Demo/Symbols").and_return({
        "Parameter": {
            "Name": "/Demo/Symbols",
            "Type": "StringList",
            "Value": "amzn,  msft "
        }
    }).once()
    flexmock(boto3).should_receive("client").with_args(
        "ssm",
        region_name="us-west-2"
    ).and_return(fake_client).once()

    assert index.get_stock_symbols() == ["AMZN", "MSFT"]


def test_send_results():
    fake_client = flexmock()
    fake_client.should_receive("publish").with_args(
        TopicArn="arn:aws:sns:us-west-2:123456789:demo",
        Message="\n{}".format("\n".join(EXPECTED_RESULTS))
    ).once()
    flexmock(boto3).should_receive("client").with_args("sns").and_return(fake_client).once()

    index.send_results(EXPECTED_RESULTS, "123456789")


def test_stock_tracker_handler_bad_ticker():
    bad_event = {"symbol": "gdd&"}
    with pytest.raises(ValueError):
        index.stock_tracker_handler(bad_event, None)

def test_stock_tracker_handler_bad_resp():
    event = {"symbol": "gddy"}
    fake_req = flexmock(ok=False, status_code=418)
    fake_req.should_receive("raise_for_status").and_raise(HTTPError("no bueno")).once()
    flexmock(requests).should_receive("get").with_args(FAKE_URI,
                                                       timeout=5).and_return(fake_req).once()

    with pytest.raises(HTTPError):
        index.stock_tracker_handler(event, None)


def test_stock_tracker_handler_empty_resp():
    event = {"symbol": "gddy"}
    fake_req = flexmock(ok=True, status_code=200)
    fake_req.should_receive("json").and_return({
        "Global Quote": {}
    }).once()
    flexmock(requests).should_receive("get").with_args(FAKE_URI,
                                                       timeout=5).and_return(fake_req).once()

    with pytest.raises(ValueError):
        index.stock_tracker_handler(event, None)


def test_stock_tracker_handler_with_event():
    event = {"symbol": "gddy"}
    fake_req = flexmock(ok=True, status_code=200)
    fake_req.should_receive("json").and_return({
        "Global Quote": {
            "01. symbol": "GDDY",
            "02. open": "74.6200",
            "03. high": "75.4250",
            "04. low": "73.9200",
            "05. price": "75.1100",
            "06. volume": "1121316",
            "07. latest trading day": "2019-03-28",
            "08. previous close": "74.2100",
            "09. change": "0.9000",
            "10. change percent": "1.2128%"
        }
    }).once()
    flexmock(requests).should_receive("get").with_args(FAKE_URI,
                                                       timeout=5).and_return(fake_req).once()

    flexmock(index).should_receive("send_results").with_args(EXPECTED_RESULTS,
                                                             "123456789").and_return(None).once()

    fake_context = flexmock(
        invoked_function_arn="arn:aws:lambda:us-west-2:123456789:function:demo"
    )
    assert index.stock_tracker_handler(event, fake_context) == EXPECTED_RESULTS
