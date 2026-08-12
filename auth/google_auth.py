"""
Google OAuth2 Authentication Module
Handles the OAuth flow, token storage and refresh.
"""
import os
from typing import Optional
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "token.json")
CREDS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")


def get_credentials() -> Optional[Credentials]:
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
            creds = _run_oauth_flow(creds_path)
            if not creds:
                return None

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return creds


def _run_oauth_flow(creds_path: str) -> Optional[Credentials]:
    """
    Run the OAuth2 installed-app flow using a fixed local redirect port.
    Uses http://localhost:8085 — no SSL, no port=0 race condition.
    Falls back to copy-paste if the local server can't bind.
    """
    import socket
    import threading
    import webbrowser
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs

    REDIRECT_PORT = 8085
    REDIRECT_URI  = f"http://localhost:{REDIRECT_PORT}"

    flow = InstalledAppFlow.from_client_secrets_file(
        creds_path, SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt="consent")

    code_holder: list = []
    server_error: list = []

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            if "code" in params:
                code_holder.append(params["code"][0])
                body = b"<h2>\u2705 \u0110\u0103ng nh\u1eadp th\u00e0nh c\u00f4ng! B\u1ea1n c\u00f3 th\u1ec3 \u0111\u00f3ng tab n\u00e0y.</h2>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
            else:
                error = params.get("error", ["unknown"])[0]
                server_error.append(error)
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Auth error: " + error.encode())

        def log_message(self, *args):
            pass  # silence request logs

    # Try to bind local HTTP server
    try:
        httpd = HTTPServer(("localhost", REDIRECT_PORT), _Handler)
    except OSError:
        # Port busy — fallback to copy-paste
        print(f"\n[auth] Mở link sau trong trình duyệt:\n{auth_url}\n")
        code = input("[auth] Dán authorization code vào đây: ").strip()
        flow.fetch_token(code=code)
        return flow.credentials

    def _serve():
        httpd.handle_request()   # one request only

    t = threading.Thread(target=_serve, daemon=True)
    t.start()

    webbrowser.open(auth_url)
    print("[auth] Đang chờ đăng nhập Google trên trình duyệt...")

    t.join(timeout=120)
    httpd.server_close()

    if server_error:
        print(f"[auth] ❌ Lỗi OAuth: {server_error[0]}")
        return None
    if not code_holder:
        print("[auth] ❌ Hết thời gian chờ. Thử lại.")
        return None

    flow.fetch_token(code=code_holder[0])
    return flow.credentials


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
