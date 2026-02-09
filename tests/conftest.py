import os

# Set test environment variables before any app imports
os.environ["WHATSAPP_VERIFY_TOKEN"] = "test_verify_token"
os.environ["WHATSAPP_ACCESS_TOKEN"] = "test_access_token"
os.environ["WHATSAPP_PHONE_NUMBER_ID"] = "123456789"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test_supabase_key"
os.environ["SUPABASE_SERVICE_KEY"] = "test_service_key"

import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()
