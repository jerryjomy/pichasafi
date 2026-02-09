import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.config import Config
from app import database as db
from app import messenger
from app import onboarding
from app import billing
from app.image_processor import process_product_photo

logger = logging.getLogger(__name__)
webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.route("/health", methods=["GET"])
def health():
    """Simple health endpoint for Railway healthcheck."""
    return "ok", 200


@webhook_bp.route("/webhook", methods=["GET"])
def verify():
    """WhatsApp webhook verification (called once during Meta setup)."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == Config.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return challenge, 200

    logger.warning(f"Webhook verification failed. mode={mode}")
    return "Forbidden", 403


@webhook_bp.route("/webhook", methods=["POST"])
def handle_message():
    """
    Main webhook handler for all incoming WhatsApp messages.
    Always returns 200 to prevent WhatsApp retries.
    """
    body = request.get_json()

    if not body:
        return jsonify({"status": "ok"}), 200

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return jsonify({"status": "ok"}), 200

        message = messages[0]
        phone = message["from"]
        message_id = message["id"]
        message_type = message["type"]

        messenger.mark_as_read(message_id)

        message_body = None
        media_id = None
        caption = None

        if message_type == "text":
            message_body = message["text"]["body"]
        elif message_type == "image":
            media_id = message["image"]["id"]
            caption = message["image"].get("caption", "")
        elif message_type == "interactive":
            interactive = message["interactive"]
            if interactive["type"] == "button_reply":
                message_body = interactive["button_reply"]["id"]
            elif interactive["type"] == "list_reply":
                message_body = interactive["list_reply"]["id"]
        else:
            messenger.send_text(
                phone,
                "I can only process text messages and images for now. "
                "Send a product photo or type *help*.",
            )
            return jsonify({"status": "ok"}), 200

        _route_message(phone, message_type, message_body, media_id, caption)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)

    return jsonify({"status": "ok"}), 200


def _route_message(
    phone: str,
    message_type: str,
    message_body: str,
    media_id: str,
    caption: str,
) -> None:
    """
    Core routing logic:
    1. New user → create + start onboarding
    2. Onboarding incomplete → continue onboarding
    3. Text command → handle command
    4. Image → process product photo
    """
    user = db.get_user_by_phone(phone)
    if not user:
        user = db.create_user(phone)
        logger.info(f"New user created: {phone}")

    if user["onboarding_step"] != "complete":
        onboarding.handle_onboarding(
            phone, user, message_type, message_body, media_id
        )
        return

    if message_type == "text" and message_body:
        command = message_body.strip().lower()

        if command == "help":
            _send_help(phone)
            return
        if command == "status":
            messenger.send_text(phone, billing.get_usage_message(phone))
            return
        if command in ("edit", "edit brand", "edit profile"):
            db.update_user(phone, {"onboarding_step": "new"})
            onboarding.handle_onboarding(
                phone,
                {**user, "onboarding_step": "new"},
                message_type,
                message_body,
            )
            return

        messenger.send_text(
            phone,
            f'I didn\'t understand "{message_body}".\n\n'
            "Send me a *product photo* to enhance it, "
            "or type *help* to see available commands.",
        )
        return

    if message_type == "image" and media_id:
        _handle_product_image(phone, user, media_id, caption)
        return


def _handle_product_image(
    phone: str, user: dict, media_id: str, caption: str
) -> None:
    """Download, process, and send back an enhanced product photo."""
    usage = billing.check_usage(phone)
    if not usage["allowed"]:
        messenger.send_text(phone, billing.get_limit_reached_message())
        return

    messenger.send_text(phone, "Processing your image...\nThis may take 15-30 seconds.")

    try:
        image_bytes = messenger.download_media(media_id)

        result_bytes = process_product_photo(
            image_bytes,
            bg_color=user.get("brand_color_bg") or "#1A1A2E",
        )

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        original_url = db.upload_to_storage(
            f"originals/{phone}/{ts}.jpg", image_bytes
        )
        result_url = db.upload_to_storage(
            f"generated/{phone}/{ts}.jpg", result_bytes
        )

        db.save_generated_image(
            user_id=user["id"],
            image_type="product_enhance",
            original_url=original_url,
            result_url=result_url,
        )

        billing.record_usage(phone)
        usage = billing.check_usage(phone)

        messenger.send_image(
            phone,
            result_url,
            caption=(
                f"Here's your enhanced product photo!\n"
                f"Images remaining: {usage['remaining']}/{usage['limit']}"
            ),
        )

    except Exception as e:
        logger.error(f"Image processing failed for {phone}: {e}", exc_info=True)
        messenger.send_text(
            phone,
            "Sorry, something went wrong processing your image.\n"
            "Please try again with a different photo.\n\n"
            "Tips for best results:\n"
            "- Use good lighting\n"
            "- Place product on a plain background\n"
            "- Make sure the product fills most of the frame",
        )


def _send_help(phone: str) -> None:
    """Send help message with available commands."""
    messenger.send_text(
        phone,
        "*PichaSafi Help*\n\n"
        "Send a *product photo* — I'll enhance it with a professional background\n\n"
        "*Commands:*\n"
        "- *help* — Show this message\n"
        "- *status* — See your usage this month\n"
        "- *edit* — Update your brand profile\n\n"
        "Tips for best photos:\n"
        "- Good lighting\n"
        "- Plain background\n"
        "- Product fills the frame\n\n"
        "More features coming soon!",
    )
