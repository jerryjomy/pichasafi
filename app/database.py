from __future__ import annotations

import logging
from supabase import create_client, Client
from app.config import Config

logger = logging.getLogger(__name__)

_client: Client = None
_service_client: Client = None


def get_client() -> Client:
    """Lazy singleton Supabase client (anon key — respects RLS)."""
    global _client
    if _client is None:
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_KEY
        logger.info(f"Connecting to Supabase: url={url}, key={key[:20]}...{key[-10:]} (len={len(key)})")
        _client = create_client(url, key)
    return _client


def get_service_client() -> Client:
    """Lazy singleton Supabase client (service role key — bypasses RLS)."""
    global _service_client
    if _service_client is None:
        url = Config.SUPABASE_URL
        key = Config.SUPABASE_SERVICE_KEY
        logger.info("Connecting to Supabase with service role key")
        _service_client = create_client(url, key)
    return _service_client


# --- User Operations ---


def get_user_by_phone(phone_number: str) -> dict | None:
    """Fetch user by WhatsApp phone number. Returns None if not found."""
    response = (
        get_client()
        .table("users")
        .select("*")
        .eq("phone_number", phone_number)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def create_user(phone_number: str) -> dict:
    """Create a new user with onboarding_step='new'."""
    response = (
        get_client()
        .table("users")
        .insert({"phone_number": phone_number, "onboarding_step": "new"})
        .execute()
    )
    return response.data[0]


def update_user(phone_number: str, updates: dict) -> dict | None:
    """Update user fields by phone number."""
    response = (
        get_client()
        .table("users")
        .update(updates)
        .eq("phone_number", phone_number)
        .execute()
    )
    return response.data[0] if response.data else None


def increment_image_count(phone_number: str) -> dict | None:
    """Increment the user's monthly image counter by 1."""
    user = get_user_by_phone(phone_number)
    if not user:
        return None
    new_count = user["images_created_this_month"] + 1
    return update_user(phone_number, {"images_created_this_month": new_count})


# --- Generated Image Operations ---


def save_generated_image(
    user_id: str,
    image_type: str,
    original_url: str,
    result_url: str,
    template_used: str = None,
    metadata: dict = None,
) -> dict:
    """Record a generated image in the database."""
    response = (
        get_client()
        .table("generated_images")
        .insert(
            {
                "user_id": user_id,
                "image_type": image_type,
                "template_used": template_used,
                "original_image_url": original_url,
                "result_image_url": result_url,
                "metadata": metadata or {},
            }
        )
        .execute()
    )
    return response.data[0]


# --- Storage Operations ---


def upload_to_storage(
    bucket_path: str, file_bytes: bytes, content_type: str = "image/jpeg"
) -> str:
    """Upload bytes to Supabase Storage. Returns the public URL.
    Uses service role key to bypass RLS policies."""
    client = get_service_client()
    client.storage.from_("pichasafi").upload(
        path=bucket_path,
        file=file_bytes,
        file_options={"content-type": content_type},
    )
    return client.storage.from_("pichasafi").get_public_url(bucket_path)
