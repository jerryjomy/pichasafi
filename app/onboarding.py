from __future__ import annotations

import logging
from datetime import datetime, timezone
from app import database as db
from app import messenger

logger = logging.getLogger(__name__)

# Color presets
COLOR_MAP = {
    "1": "#FF6B00",  # Orange
    "2": "#0066FF",  # Blue
    "3": "#00AA44",  # Green
    "4": "#CC0000",  # Red
    "5": "#8800CC",  # Purple
}

# Style presets
STYLE_MAP = {
    "1": "modern",
    "2": "bold",
    "3": "elegant",
}

WELCOME_MESSAGE = (
    "Karibu PichaSafi!\n\n"
    "I'll help you create stunning marketing visuals for your business.\n\n"
    "Let's set up your brand profile (takes 2 minutes).\n\n"
    "What is your *business name*?"
)

ASK_LOGO = (
    "Now send me your *business logo* (as an image).\n\n"
    "If you don't have one yet, type *skip*."
)

ASK_LOCATION = "Where is your business located?\n\n(e.g., Dar es Salaam, Arusha, Nairobi)"

ASK_CONTACT = (
    "What phone number should appear on your marketing materials?\n\n"
    "(e.g., +255 712 345 678)"
)

ASK_COLORS = (
    "Choose your brand's primary color:\n\n"
    "1 - Orange (#FF6B00)\n"
    "2 - Blue (#0066FF)\n"
    "3 - Green (#00AA44)\n"
    "4 - Red (#CC0000)\n"
    "5 - Purple (#8800CC)\n"
    "6 - Custom (send hex code like #FF6B00)\n\n"
    "Reply with a number or hex code."
)

ASK_STYLE = (
    "Choose your design style:\n\n"
    "1 - Modern (clean, minimal)\n"
    "2 - Bold (high contrast, impactful)\n"
    "3 - Elegant (refined, premium)\n\n"
    "Reply with a number."
)


def handle_onboarding(
    phone: str,
    user: dict,
    message_type: str,
    message_body: str = None,
    media_id: str = None,
) -> None:
    """
    Process an onboarding step based on user's current onboarding_step.
    Called by the webhook handler when onboarding_step != 'complete'.
    """
    step = user["onboarding_step"]

    if step == "new":
        messenger.send_text(phone, WELCOME_MESSAGE)
        db.update_user(phone, {"onboarding_step": "name"})
        return

    if step == "name":
        if not message_body or not message_body.strip():
            messenger.send_text(phone, "Please type your business name.")
            return
        db.update_user(phone, {
            "business_name": message_body.strip(),
            "onboarding_step": "logo",
        })
        messenger.send_text(phone, ASK_LOGO)
        return

    if step == "logo":
        if message_type == "image" and media_id:
            try:
                logo_bytes = messenger.download_media(media_id)
                ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                filename = f"logos/{phone}_{ts}.jpg"
                logo_url = db.upload_to_storage(filename, logo_bytes)
                db.update_user(phone, {
                    "logo_url": logo_url,
                    "onboarding_step": "location",
                })
                messenger.send_text(phone, f"Logo saved!\n\n{ASK_LOCATION}")
            except Exception as e:
                logger.error(f"Logo upload failed for {phone}: {e}")
                messenger.send_text(
                    phone,
                    "Sorry, couldn't save that image. Please try again or type *skip*.",
                )
            return
        if message_body and message_body.strip().lower() == "skip":
            db.update_user(phone, {"onboarding_step": "location"})
            messenger.send_text(
                phone, f"No worries! You can add a logo later.\n\n{ASK_LOCATION}"
            )
            return
        messenger.send_text(phone, "Please send your logo as an image, or type *skip*.")
        return

    if step == "location":
        if not message_body or not message_body.strip():
            messenger.send_text(phone, "Please type your business location.")
            return
        db.update_user(phone, {
            "location": message_body.strip(),
            "onboarding_step": "contact",
        })
        messenger.send_text(phone, ASK_CONTACT)
        return

    if step == "contact":
        if not message_body or not message_body.strip():
            messenger.send_text(phone, "Please type a contact phone number.")
            return
        db.update_user(phone, {
            "contact_phone": message_body.strip(),
            "contact_whatsapp": phone,
            "onboarding_step": "colors",
        })
        messenger.send_text(phone, ASK_COLORS)
        return

    if step == "colors":
        color = _parse_color(message_body)
        if not color:
            messenger.send_text(
                phone, "Please reply with a number (1-5) or a hex code (e.g., #FF6B00)."
            )
            return
        db.update_user(phone, {
            "brand_color_primary": color,
            "onboarding_step": "style",
        })
        messenger.send_text(phone, f"Brand color set to {color}\n\n{ASK_STYLE}")
        return

    if step == "style":
        style = STYLE_MAP.get(message_body.strip() if message_body else "")
        if not style:
            messenger.send_text(phone, "Please reply with 1, 2, or 3.")
            return

        db.update_user(phone, {
            "template_style": style,
            "onboarding_step": "complete",
        })

        # Refresh user data for the completion message
        user = db.get_user_by_phone(phone)
        messenger.send_text(
            phone,
            f"You're all set, {user['business_name']}!\n\n"
            f"Your brand profile:\n"
            f"Location: {user['location']}\n"
            f"Contact: {user['contact_phone']}\n"
            f"Color: {user['brand_color_primary']}\n"
            f"Style: {style.title()}\n\n"
            f"You have *{user['monthly_limit']} free images* to start.\n\n"
            f"*To get started:* Send me a product photo and I'll make it look professional!\n\n"
            f"Type *help* anytime to see what I can do.",
        )
        return


def _parse_color(text: str) -> str | None:
    """Parse a color choice: number (1-5) or hex code."""
    if not text:
        return None
    text = text.strip()
    if text in COLOR_MAP:
        return COLOR_MAP[text]
    if text.startswith("#") and len(text) == 7:
        try:
            int(text[1:], 16)
            return text.upper()
        except ValueError:
            pass
    return None
