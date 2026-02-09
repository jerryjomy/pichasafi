from __future__ import annotations

import logging
import requests
from app.config import Config

logger = logging.getLogger(__name__)


def _get_headers() -> dict:
    """Build auth headers lazily so token is read at call time, not import time."""
    return {
        "Authorization": f"Bearer {Config.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _send(payload: dict) -> dict:
    """Send a message via WhatsApp Cloud API."""
    try:
        response = requests.post(
            Config.WHATSAPP_API_URL,
            headers=_get_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"WhatsApp API error: {e}")
        return {"error": str(e)}


def send_text(to: str, message: str) -> dict:
    """Send a plain text message."""
    return _send(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }
    )


def send_image(to: str, image_url: str, caption: str = "") -> dict:
    """Send an image by public URL with optional caption."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url},
    }
    if caption:
        payload["image"]["caption"] = caption
    return _send(payload)


def send_buttons(to: str, body_text: str, buttons: list[dict]) -> dict:
    """
    Send an interactive button message.
    buttons: list of {"id": "btn_id", "title": "Button Text"} (max 3)
    """
    return _send(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": btn} for btn in buttons[:3]
                    ]
                },
            },
        }
    )


def send_list(to: str, body_text: str, button_text: str, sections: list[dict]) -> dict:
    """Send an interactive list message for menus and selections."""
    return _send(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": button_text,
                    "sections": sections,
                },
            },
        }
    )


def mark_as_read(message_id: str) -> dict:
    """Mark an incoming message as read (blue ticks)."""
    return _send(
        {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
    )


def download_media(media_id: str) -> bytes:
    """
    Download media from WhatsApp. Two-step process:
    1. GET media URL from media_id
    2. GET the actual binary from that URL
    """
    auth_headers = {"Authorization": f"Bearer {Config.WHATSAPP_ACCESS_TOKEN}"}

    # Step 1: Get the download URL
    url = f"{Config.WHATSAPP_MEDIA_URL}/{media_id}"
    resp = requests.get(url, headers=auth_headers, timeout=15)
    resp.raise_for_status()
    media_url = resp.json().get("url")

    # Step 2: Download the actual file
    media_resp = requests.get(media_url, headers=auth_headers, timeout=60)
    media_resp.raise_for_status()
    return media_resp.content
