"""
Google OAuth2 Authentication Module
Handles the OAuth flow, token storage and refresh.
"""
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "token.json")
CREDS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")


def get_credentials() -> Credentials | None:
    """Load existing credentials or run OAuth flow if needed."""
    token_path = os.path.abspath(TOKEN_FILE)
    creds_path = os.path.abspath(CREDS_FILE)
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(creds_path):
                return None  # Credentials file not set up yet
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return creds


def is_authenticated() -> bool:
    """Check if valid credentials exist without triggering a new flow."""
    token_path = os.path.abspath(TOKEN_FILE)
    if not os.path.exists(token_path):
        return False
    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds.valid:
            return True
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            return True
    except Exception:
        pass
    return False


def revoke_credentials():
    """Remove saved token to force re-authentication."""
    token_path = os.path.abspath(TOKEN_FILE)
    if os.path.exists(token_path):
        os.remove(token_path)


def get_user_info(creds: Credentials) -> dict:
    """Fetch basic user info (name, email) from Google."""
    from googleapiclient.discovery import build
    try:
        service = build("oauth2", "v2", credentials=creds)
        info = service.userinfo().get().execute()
        return info
    except Exception:
        return {}
