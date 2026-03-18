import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _send_embed(embed: dict) -> bool:
    """Send a Discord embed message via webhook. Returns True on success."""
    url = settings.discord_webhook_url
    if not url:
        logger.debug("Discord webhook URL not configured — skipping notification")
        return False

    try:
        response = httpx.post(
            url,
            json={"embeds": [embed]},
            headers={"Content-Type": "application/json"},
            timeout=10.0,
        )
        if response.status_code in (200, 204):
            logger.info("Discord notification sent successfully")
            return True
        logger.warning("Discord webhook returned %s: %s", response.status_code, response.text[:200])
        return False
    except httpx.HTTPError:
        logger.exception("Failed to send Discord notification")
        return False


def notify_enrollment(username: str, course_name: str) -> bool:
    """Send a Discord notification when a student enrolls in a course."""
    embed = {
        "title": "📚 Új beiratkozás",
        "description": f"**{username}** beiratkozott a **{course_name}** kurzusra.",
        "color": 0x3498DB,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return _send_embed(embed)


def notify_certificate(username: str, course_name: str, cert_id: str) -> bool:
    """Send a Discord notification when a certificate is issued."""
    verify_url = f"{settings.base_url}/verify/{cert_id}"
    embed = {
        "title": "🎓 Tanúsítvány kiállítva",
        "description": f"**{username}** megszerezte a **{course_name}** kurzus tanúsítványát!",
        "color": 0x2ECC71,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {"name": "Hitelesítés", "value": verify_url, "inline": False},
        ],
    }
    return _send_embed(embed)
