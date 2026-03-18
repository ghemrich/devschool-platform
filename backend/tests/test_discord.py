from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.discord import _send_embed, notify_certificate, notify_enrollment


class TestSendEmbed:
    """Tests for the low-level _send_embed helper."""

    @patch("app.services.discord.settings")
    def test_skips_when_no_webhook_url(self, mock_settings):
        mock_settings.discord_webhook_url = ""
        assert _send_embed({"title": "test"}) is False

    @patch("app.services.discord.settings")
    @patch("app.services.discord.httpx.post")
    def test_sends_embed_successfully(self, mock_post, mock_settings):
        mock_settings.discord_webhook_url = "https://discord.com/api/webhooks/test"
        mock_post.return_value = MagicMock(status_code=204)
        assert _send_embed({"title": "test"}) is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["embeds"][0]["title"] == "test"

    @patch("app.services.discord.settings")
    @patch("app.services.discord.httpx.post")
    def test_returns_false_on_http_error(self, mock_post, mock_settings):
        mock_settings.discord_webhook_url = "https://discord.com/api/webhooks/test"
        mock_post.side_effect = httpx.ConnectError("connection refused")
        assert _send_embed({"title": "test"}) is False

    @patch("app.services.discord.settings")
    @patch("app.services.discord.httpx.post")
    def test_returns_false_on_non_success_status(self, mock_post, mock_settings):
        mock_settings.discord_webhook_url = "https://discord.com/api/webhooks/test"
        mock_post.return_value = MagicMock(status_code=400, text="Bad Request")
        assert _send_embed({"title": "test"}) is False


class TestNotifyEnrollment:
    """Tests for enrollment notifications."""

    @patch("app.services.discord._send_embed")
    def test_sends_enrollment_embed(self, mock_send):
        mock_send.return_value = True
        result = notify_enrollment("student1", "Python 101")
        assert result is True
        mock_send.assert_called_once()
        embed = mock_send.call_args[0][0]
        assert "student1" in embed["description"]
        assert "Python 101" in embed["description"]
        assert embed["color"] == 0x3498DB

    @patch("app.services.discord._send_embed")
    def test_returns_false_when_send_fails(self, mock_send):
        mock_send.return_value = False
        assert notify_enrollment("student1", "Python 101") is False


class TestNotifyCertificate:
    """Tests for certificate notifications."""

    @patch("app.services.discord.settings")
    @patch("app.services.discord._send_embed")
    def test_sends_certificate_embed(self, mock_send, mock_settings):
        mock_settings.base_url = "https://openschool.example.com"
        mock_send.return_value = True
        result = notify_certificate("student1", "Python 101", "abc-123")
        assert result is True
        mock_send.assert_called_once()
        embed = mock_send.call_args[0][0]
        assert "student1" in embed["description"]
        assert "Python 101" in embed["description"]
        assert embed["color"] == 0x2ECC71
        assert any("abc-123" in f["value"] for f in embed["fields"])

    @patch("app.services.discord.settings")
    @patch("app.services.discord._send_embed")
    def test_returns_false_when_send_fails(self, mock_send, mock_settings):
        mock_settings.base_url = "https://openschool.example.com"
        mock_send.return_value = False
        assert notify_certificate("student1", "Python 101", "abc-123") is False
