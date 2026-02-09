import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # WhatsApp Cloud API
    WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")
    WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_API_URL = ""  # Set in validate()
    WHATSAPP_MEDIA_URL = "https://graph.facebook.com/v21.0"

    # Supabase
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

    # App
    APP_URL = os.environ.get("APP_URL", "http://localhost:5000")
    FREE_IMAGE_LIMIT = int(os.environ.get("FREE_IMAGE_LIMIT", "3"))

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FONTS_DIR = os.path.join(BASE_DIR, "fonts")
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

    @classmethod
    def validate(cls):
        """Raise on missing required environment variables."""
        required = [
            "WHATSAPP_VERIFY_TOKEN",
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID",
            "SUPABASE_URL",
            "SUPABASE_KEY",
        ]
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        # Compute derived values after env vars are confirmed
        cls.WHATSAPP_API_URL = (
            f"https://graph.facebook.com/v21.0/{cls.WHATSAPP_PHONE_NUMBER_ID}/messages"
        )
