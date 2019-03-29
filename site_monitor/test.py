import copy

from flexmock import flexmock

from . import index

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
STAT_LIST[0]["response_time"] = 100
STAT_LIST[1]["check_time"] = "2019-03-29T13:06:12.102297"
STAT_LIST[1]["response_code"] = 200
STAT_LIST[1]["response_time"] = 50


def test_get_sites():
    mock = flexmock()
    mock.should_receive("scan").with_args(TableName="demo", ConsistentRead=True).and_return({
        "Items": [
            {"is_down": {"BOOL": True}, "site_id": {"N": "1"}, "site_name": {"S": "mock.io"}},
            {"is_down": {"BOOL": False}, "site_id": {"N": "2"}, "site_name": {"S": "mock.com"}}
        ]
    }).once()

    assert index.get_sites(mock) == SITE_LIST

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
            "response_time": {"N": "100"}
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
            "response_time": {"N": "50"}
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

    index.send_alert(fake_client, "123456789", [STAT_LIST[0]])
    index.send_alert(fake_client, "123456789", [])
