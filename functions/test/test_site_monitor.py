import boto3
from flexmock import flexmock
from freezegun import freeze_time
import requests
from requests.exceptions import ReadTimeout

from src.SiteMonitor import index

SITE_LIST = ["mock.io", "mock.com"]

MOCK_RESULTS = [
    {
        "name": "mock.io",
        "check_time": "2019-04-11T22:44:55-07:00",
        "is_down": False,
        "response_code": 200,
        "response_time": 0.1
    },
    {
        "name": "mock.com",
        "check_time": "2019-04-11T22:44:55-07:00",
        "is_down": True,
        "response_code": 504,
        "response_time": 3
    }
]


def test_get_sites():
    fake_client = flexmock()
    fake_client.should_receive("get_parameter").with_args(Name="/Demo/Sites").and_return({
        "Parameter": {
            "Name": "/Demo/Symbols",
            "Type": "StringList",
            "Value": "mock.io,  mock.COM "
        }
    }).once()
    flexmock(boto3).should_receive("client").with_args(
        "ssm",
        region_name="us-west-2"
    ).and_return(fake_client).once()

    assert index.get_sites() == SITE_LIST


def test_save_stats():
    fake_client = flexmock()
    fake_client.should_receive("put_item").with_args(
        TableName="demo",
        Item={
            "name": {"S": "mock.io"},
            "timestamp": {"S": "2019-04-11T22:44:55-07:00"},
            "is_down": {"BOOL": False},
            "response_code": {"N": "200"},
            "response_time": {"N": "0.1"}
        }
    ).once()
    fake_client.should_receive("put_item").with_args(
        TableName="demo",
        Item={
            "name": {"S": "mock.com"},
            "timestamp": {"S": "2019-04-11T22:44:55-07:00"},
            "is_down": {"BOOL": True},
            "response_code": {"N": "504"},
            "response_time": {"N": "3"}
        }
    ).once()
    flexmock(boto3).should_receive("client").with_args(
        "dynamodb",
        region_name="us-west-2"
    ).and_return(fake_client).once()

    index.save_stats(MOCK_RESULTS)


@freeze_time("2019-04-12 05:44:55")
def test_site_monitor_handler():
    flexmock(index).should_receive("get_sites").and_return(SITE_LIST).once()
    mock_timing = flexmock()
    mock_timing.should_receive("total_seconds").and_return(0.1).once()
    fake_resp = flexmock(status_code=200, elapsed=mock_timing)
    flexmock(requests).should_receive("get").with_args("https://mock.io", timeout=index.MAX_TIME)\
                                            .and_return(fake_resp).once()
    flexmock(requests).should_receive("get").with_args("https://mock.com", timeout=index.MAX_TIME)\
                                            .and_raise(ReadTimeout()).once()
    flexmock(index).should_receive("save_stats").with_args(MOCK_RESULTS).and_return(None).once()

    assert index.site_monitor_handler(None, None) is None
