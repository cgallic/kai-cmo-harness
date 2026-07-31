from pathlib import Path
import sys
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.connectors.social.base import SocialConnectorConfig, SocialPost
from kai.connectors.social.outstand import OutstandConnector


def connector(**metadata):
    return OutstandConnector(SocialConnectorConfig(platform="outstand", access_token="token", page_id="acct_1", sandbox_mode=False, metadata=metadata))


def test_list_accounts_and_connect_read_back():
    c = connector()
    c._api_call = Mock(return_value={"data": [{"id": "acct_1", "name": "Main"}]})
    assert c.connect() is True
    assert c.list_accounts()[0]["id"] == "acct_1"
    assert c._api_call.call_args.args[:2] == ("GET", "https://api.outstand.so/v1/social-accounts")


def test_create_scheduled_post_sends_idempotency_and_read_back():
    c = connector()
    c._connected = True
    c._api_call = Mock(side_effect=[{"data": {"id": "post_1", "status": "scheduled", "scheduled_at": "2026-08-01T12:00:00Z"}}, {"data": {"id": "post_1", "content": "hello", "status": "scheduled"}}])
    post = c.create_post(SocialPost(platform="outstand", content_text="hello", schedule_time="2026-08-01T12:00:00Z"))
    assert post.id == "post_1"
    assert post.status == "scheduled"
    assert c._api_call.call_args_list[0].kwargs["headers"]["Idempotency-Key"] == post.metadata["idempotency_key"]
    assert c.get_post("post_1").id == "post_1"


def test_validation_and_provider_errors_are_clear_and_idempotent():
    c = connector()
    c._connected = True
    too_many = SocialPost(platform="outstand", content_text="x", hashtags=[str(i) for i in range(31)])
    assert c.create_post(too_many).error_message.startswith("Hashtag count")
    c._api_call = Mock(side_effect=RuntimeError("provider unavailable"))
    failed = c.create_post(SocialPost(platform="outstand", content_text="hello"))
    assert failed.status == "failed"
    assert failed.error_message == "provider unavailable"
