from . import index

import pytest
from flexmock import flexmock
import requests
from requests.exceptions import HTTPError

FAKE_URI = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=GDDY&apikey=demo"

def test_stock_tracker_handler_bad_ticker():
    bad_event = {"symbol": "gdd&"}
    with pytest.raises(ValueError):
        index.stock_tracker_handler(bad_event, None)

def test_stock_tracker_handler_bad_resp():
    event = {"symbol": "gddy"}
    fake_req = flexmock(ok=False, status_code=418)
    fake_req.should_receive("raise_for_status").and_raise(HTTPError("no bueno")).once()
    flexmock(requests).should_receive("get").with_args(FAKE_URI).and_return(fake_req).once()

    with pytest.raises(HTTPError):
        index.stock_tracker_handler(event, None)

def test_stock_tracker_handler():
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
    flexmock(requests).should_receive("get").with_args(FAKE_URI).and_return(fake_req).once()

    assert index.stock_tracker_handler(event, None) == "GDDY: 75.11 +0.90 (+1.21%)"
