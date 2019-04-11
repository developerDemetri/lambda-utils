import copy

import boto3
from flexmock import flexmock
import requests
from requests.exceptions import ReadTimeout

from src.SiteMonitor import index

SITE_LIST = [
    {
        "id": 1,
        "name": "mock.io",
        "is_down": True
    },
    {
        "id": 2,
        "name": "mock.com",
        "is_down": False
    }
]

STAT_LIST = copy.deepcopy(SITE_LIST)
STAT_LIST[0]["check_time"] = "2019-03-29T13:05:38.876628"
STAT_LIST[0]["response_code"] = 418
STAT_LIST[0]["response_time"] = 0.1
STAT_LIST[1]["check_time"] = "2019-03-29T13:06:12.102297"
STAT_LIST[1]["response_code"] = 200
STAT_LIST[1]["response_time"] = 0.5


def test_get_sites():
    fake_client = flexmock()
    fake_client.should_receive("scan").with_args(
        TableName="demo", ConsistentRead=True
    ).and_return({"Items": [
        {"is_down": {"BOOL": True}, "site_id": {"N": "1"}, "site_name": {"S": "mock.io"}},
        {"is_down": {"BOOL": False}, "site_id": {"N": "2"}, "site_name": {"S": "mock.com"}}
    ]}).once()

    assert index.get_sites(fake_client) == SITE_LIST


def test_save_stats():
    fake_client = flexmock()
    fake_client.should_receive("update_item").with_args(
        TableName="demo",
        Key={"site_id": {"N": "1"}},
        UpdateExpression="SET is_down = :val",
        ExpressionAttributeValues={":val": {"BOOL": True}}
    ).once()
    fake_client.should_receive("update_item").with_args(
        TableName="demo",
        Key={"site_id": {"N": "2"}},
        UpdateExpression="SET is_down = :val",
        ExpressionAttributeValues={":val": {"BOOL": False}}
    ).once()
    fake_client.should_receive("put_item").with_args(
        TableName="demo",
        Item={
            "site_id": {"N": "1"},
            "site_name": {"S": "mock.io"},
            "timestamp": {"S": "2019-03-29T13:05:38.876628"},
            "is_down": {"BOOL": True},
            "response_code": {"N": "418"},
            "response_time": {"N": "0.1"}
        }
    ).once()
    fake_client.should_receive("put_item").with_args(
        TableName="demo",
        Item={
            "site_id": {"N": "2"},
            "site_name": {"S": "mock.com"},
            "timestamp": {"S": "2019-03-29T13:06:12.102297"},
            "is_down": {"BOOL": False},
            "response_code": {"N": "200"},
            "response_time": {"N": "0.5"}
        }
    ).once()

    index.save_stats(fake_client, STAT_LIST)


def test_send_alert():
    fake_client = flexmock()
    fake_client.should_receive("publish").with_args(
        TopicArn="arn:aws:sns:us-west-2:123456789:demo",
        Subject="Site Monitor Alert: Webite(s) Down",
        Message="\n".join([
            "The following site(s) returned unhealthy responses:",
            "\tmock.io\t418",
            "DeveloperDemetri Site Monitor"
        ])
    ).once()
    flexmock(boto3).should_receive("client").with_args("sns").and_return(fake_client).once()

    index.send_alert("123456789", [STAT_LIST[0]])
    index.send_alert("123456789", [])


def test_site_monitor_handler():
    mock = flexmock()
    mock.should_receive("total_seconds").and_return(0.1).and_return(0.5).and_return(0.5).times(3)
    flexmock(boto3).should_receive("client").with_args("dynamodb").and_return(mock).twice()
    flexmock(index).should_receive("get_sites").with_args(mock).and_return(SITE_LIST).twice()
    bad_resp = flexmock(status_code=418, elapsed=mock)
    good_resp = flexmock(status_code=200, elapsed=mock)
    flexmock(requests).should_receive("get").with_args("https://mock.io", timeout=index.MAX_TIME)\
                                            .and_return(bad_resp).and_raise(ReadTimeout()).twice()
    flexmock(requests).should_receive("get").with_args("https://mock.com", timeout=index.MAX_TIME)\
                                            .and_return(good_resp).twice()
    flexmock(index).should_receive("save_stats").and_return(None).twice()
    flexmock(index).should_receive("send_alert").and_return(None).twice()

    fake_context = flexmock(
        invoked_function_arn="arn:aws:lambda:us-west-2:123456789:function:demo"
    )
    assert index.site_monitor_handler(dict(), fake_context) is None
    assert index.site_monitor_handler(dict(), fake_context) is None
