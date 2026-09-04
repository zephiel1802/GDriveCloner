"""
Google OAuth2 Authentication Module
Handles the OAuth flow, token storage and refresh.

When bundled with PyInstaller, token.json is stored in the user data dir
(~/.gdrivecloner/ on macOS/Linux, %APPDATA%\\GDriveCloner\\ on Windows).
credentials.json is looked up in the user data dir first, then next to the
executable (for users who manually place it there), then the source dir.
"""
import os
import sys
from typing import Optional
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]


def _data_dir() -> str:
    """Same logic as services/config._get_data_dir — duplicated to avoid circular import."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        d = os.path.join(base, "GDriveCloner")
    else:
        d = os.path.join(os.path.expanduser("~"), ".gdrivecloner")
    os.makedirs(d, exist_ok=True)
    return d


def _exe_dir() -> str:
    """Directory of the running executable (works for both script & PyInstaller)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__ + "/.." ))


# token.json always lives in the user data dir (writable)
TOKEN_FILE = os.path.join(_data_dir(), "token.json")

# credentials.json: user data dir > exe dir > source dir
def _find_creds() -> str:
    candidates = [
        os.path.join(_data_dir(), "credentials.json"),
        os.path.join(_exe_dir(), "credentials.json"),
        os.path.join(os.path.dirname(__file__), "..", "credentials.json"),
    ]
    for path in candidates:
        if os.path.exists(os.path.abspath(path)):
            return os.path.abspath(path)
    # Return primary location (data dir) even if it doesn't exist yet
    return os.path.join(_data_dir(), "credentials.json")


CREDS_FILE = _find_creds()


def get_credentials() -> Optional[Credentials]:
    """Load existing credentials or run OAuth flow if needed."""
    # Re-resolve paths at call time (in case data dir was created after import)
    token_path = TOKEN_FILE
    creds_path = _find_creds()
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                # invalid_grant or revoked — delete stale token, force re-auth
                creds = None
                if os.path.exists(token_path):
                    os.remove(token_path)

        if not creds:
            if not os.path.exists(creds_path):
                return None  # Credentials file not set up yet
            creds = _run_oauth_flow(creds_path)
            if not creds:
                return None

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return creds


# Global OAuth session state (one login at a time)
_oauth_session: dict = {}


def start_oauth_flow(creds_path: str) -> str:
    """
    Prepare the OAuth flow: bind a local callback server, generate the
    Google auth URL and return it. The CALLER (frontend) is responsible
    for opening the URL in a browser tab.
    Call wait_oauth_flow() in a background thread to block until the
    user completes login.
    """
    import socket
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs

    global _oauth_session

    # Pick a random available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        port = s.getsockname()[1]

    redirect_uri = f"http://localhost:{port}"
    flow = InstalledAppFlow.from_client_secrets_file(
        creds_path, SCOPES, redirect_uri=redirect_uri
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
                body = b"""<!DOCTYPE html><html><head><meta charset="utf-8">
                <script>window.close();setTimeout(()=>{window.location.href='http://localhost:5001'},800);</script>
                </head><body style="font-family:sans-serif;text-align:center;padding-top:60px">
                <h2 style="color:#4CAF50">&#10003; Dang nhap thanh cong!</h2>
                <p>Dang quay lai ung dung...</p></body></html>"""
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
            pass

    httpd = HTTPServer(("localhost", port), _Handler)

    _oauth_session = {
        "flow": flow,
        "httpd": httpd,
        "code_holder": code_holder,
        "server_error": server_error,
    }
    return auth_url
    
def cancel_oauth_flow():
    """Abort the waiting OAuth flow by sending a cancellation request to the local server."""
    global _oauth_session
    if not _oauth_session:
        return
    import urllib.request
    port = _oauth_session["httpd"].server_port
    try:
        urllib.request.urlopen(f"http://localhost:{port}/?error=cancelled", timeout=1)
    except Exception:
        pass

def wait_oauth_flow() -> Optional[Credentials]:
    """
    Block until the user completes OAuth in their browser (max 120s).
    Must be called after start_oauth_flow().
    """
    global _oauth_session
    session = _oauth_session
    if not session:
        return None

    httpd       = session["httpd"]
    flow        = session["flow"]
    code_holder = session["code_holder"]
    server_error= session["server_error"]

    httpd.handle_request()   # blocks until one request arrives
    httpd.server_close()
    _oauth_session = {}

    if server_error:
        return None
    if not code_holder:
        return None

    flow.fetch_token(code=code_holder[0])
    return flow.credentials


def _run_oauth_flow(creds_path: str) -> Optional[Credentials]:
    """Legacy wrapper — kept for compatibility."""
    auth_url = start_oauth_flow(creds_path)
    print(f"[auth] Mo trinh duyet de dang nhap: {auth_url}")
    return wait_oauth_flow()


def is_authenticated() -> bool:
    """Check if valid credentials exist without triggering a new flow."""
    token_path = TOKEN_FILE
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
    token_path = TOKEN_FILE
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
