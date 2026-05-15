"""Unit tests for SlackNotifier."""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.notifier.slack_notifier import MigrationNotification, SlackNotifier


SUCCESS_NOTIFICATION = MigrationNotification(
    status="success",
    environment="staging",
    migrations_applied=3,
    migrations_list=[
        "V1__create_users_table.sql",
        "V2__add_user_profiles_table.sql",
        "V3__create_orders_table.sql",
    ],
    duration_seconds=1.23,
    branch="main",
    commit_sha="abc1234def567890",
)

FAILURE_NOTIFICATION = MigrationNotification(
    status="failure",
    environment="staging",
    migrations_applied=0,
    migrations_list=[],
    error_message="column 'email' already exists",
    migration_file="V3__create_orders_table.sql",
    branch="feature/orders",
    commit_sha="deadbeef00000000",
)


class TestSlackNotifier:
    def test_no_webhook_returns_false(self):
        notifier = SlackNotifier(webhook_url="")
        result = notifier.send(SUCCESS_NOTIFICATION)
        assert result is False

    def test_success_payload_contains_success_marker(self):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        payload = notifier._build_success_payload(SUCCESS_NOTIFICATION)
        assert "[SUCCESS]" in payload["text"]
        assert "staging" in payload["text"]
        assert "V1__create_users_table.sql" in payload["text"]

    def test_failure_payload_contains_failure_marker(self):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        payload = notifier._build_failure_payload(FAILURE_NOTIFICATION)
        assert "[FAILURE]" in payload["text"]
        assert "email" in payload["text"]
        assert "V3__create_orders_table.sql" in payload["text"]

    def test_success_payload_color_is_good(self):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        payload = notifier._build_success_payload(SUCCESS_NOTIFICATION)
        assert payload["attachments"][0]["color"] == "good"

    def test_failure_payload_color_is_danger(self):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        payload = notifier._build_failure_payload(FAILURE_NOTIFICATION)
        assert payload["attachments"][0]["color"] == "danger"

    @patch("urllib.request.urlopen")
    def test_send_success_returns_true(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        result = notifier.send(SUCCESS_NOTIFICATION)
        assert result is True

    @patch("urllib.request.urlopen")
    def test_send_failure_notification(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        result = notifier.send(FAILURE_NOTIFICATION)
        assert result is True
