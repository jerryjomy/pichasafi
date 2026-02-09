import pytest
from unittest.mock import patch, MagicMock


def test_webhook_verification(client):
    """GET /webhook should return the challenge when token matches."""
    resp = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "test_verify_token",
            "hub.challenge": "challenge_abc123",
        },
    )
    assert resp.status_code == 200
    assert resp.data.decode() == "challenge_abc123"


def test_webhook_rejects_bad_token(client):
    """GET /webhook should return 403 for wrong verify token."""
    resp = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "challenge_abc123",
        },
    )
    assert resp.status_code == 403


def test_webhook_handles_empty_post(client):
    """POST /webhook with no body should return 200."""
    resp = client.post("/webhook", json={})
    assert resp.status_code == 200


def test_webhook_handles_status_update(client):
    """POST /webhook with no messages (status update) should return 200."""
    resp = client.post(
        "/webhook",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [{"status": "delivered"}]
                            }
                        }
                    ]
                }
            ]
        },
    )
    assert resp.status_code == 200


@patch("app.webhook.onboarding")
@patch("app.webhook.messenger")
@patch("app.webhook.db")
def test_new_user_starts_onboarding(mock_db, mock_messenger, mock_onboarding, client):
    """New user sending a text message should trigger user creation + onboarding."""
    mock_db.get_user_by_phone.return_value = None
    mock_db.create_user.return_value = {
        "id": "test-uuid",
        "phone_number": "255712345678",
        "onboarding_step": "new",
    }

    resp = client.post(
        "/webhook",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "255712345678",
                                        "id": "msg_001",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )

    assert resp.status_code == 200
    mock_db.create_user.assert_called_once_with("255712345678")
    mock_onboarding.handle_onboarding.assert_called_once()


@patch("app.webhook.messenger")
@patch("app.webhook.db")
def test_help_command(mock_db, mock_messenger, client):
    """Onboarded user sending 'help' should receive help text."""
    mock_db.get_user_by_phone.return_value = {
        "id": "test-uuid",
        "phone_number": "255712345678",
        "onboarding_step": "complete",
    }

    resp = client.post(
        "/webhook",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "255712345678",
                                        "id": "msg_002",
                                        "type": "text",
                                        "text": {"body": "help"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )

    assert resp.status_code == 200
    mock_messenger.send_text.assert_called()
    # Verify help text was sent (second call, first is mark_as_read)
    help_call = mock_messenger.send_text.call_args
    assert "PichaSafi Help" in help_call[0][1]


@patch("app.webhook.messenger")
@patch("app.webhook.db")
def test_unsupported_message_type(mock_db, mock_messenger, client):
    """Unsupported message types (video, audio) should get a friendly error."""
    resp = client.post(
        "/webhook",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "255712345678",
                                        "id": "msg_003",
                                        "type": "video",
                                        "video": {"id": "vid_001"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )

    assert resp.status_code == 200
    mock_messenger.send_text.assert_called()
    error_msg = mock_messenger.send_text.call_args[0][1]
    assert "text messages and images" in error_msg
