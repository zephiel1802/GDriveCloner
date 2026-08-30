#!/usr/bin/env python3
"""
GDriveCloner - Desktop App Entry Point
Chay Flask ngam, hien thi UI trong native window (pywebview).
Khong can browser. Minimize to tray khi dong cua so.
"""
import sys
import os
import threading
import time
import logging

# Ensure bundled packages are importable (PyInstaller)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
import webview
import autostart

APP_NAME = "GDriveCloner"
APP_URL  = "http://localhost:5001"
APP_PORT = 5001

_window    = None
_tray_icon = None
_closing_to_tray = False  # flag: True means close = minimize, not quit


# ── Icon ──────────────────────────────────────────────────────────────────────
def _get_icon_image():
    base = (sys._MEIPASS if (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'))
            else os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base, 'assets', 'icon.png')
    if os.path.exists(icon_path):
        return Image.open(icon_path)
    img = Image.new('RGBA', (64, 64), (33, 150, 243, 255))
    d = ImageDraw.Draw(img)
    try:
        d.text((20, 20), "G", fill=(255, 255, 255), font=ImageFont.load_default())
    except Exception:
        pass
    return img


# ── Flask ─────────────────────────────────────────────────────────────────────
def _run_flask():
    from server import app as flask_app
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    flask_app.run(host='localhost', port=APP_PORT,
                  debug=False, use_reloader=False, threaded=True)


def _wait_for_flask(timeout=30.0):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(APP_URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


# ── Window ────────────────────────────────────────────────────────────────────
def _show_window():
    global _window
    if _window:
        try:
            _window.show()
        except Exception:
            pass


def _hide_window():
    global _window
    if _window:
        try:
            _window.hide()
        except Exception:
            pass


# ── Tray ──────────────────────────────────────────────────────────────────────
def _on_tray_open(icon, menu_item):
    _show_window()


def _on_tray_toggle_autostart(icon, menu_item):
    autostart.set_state(not autostart.is_enabled())


def _on_tray_quit(icon, menu_item):
    global _closing_to_tray
    _closing_to_tray = False  # allow real close
    icon.stop()
    try:
        if _window:
            _window.destroy()
    except Exception:
        pass
    os._exit(0)


def _build_tray():
    menu = pystray.Menu(
        item(APP_NAME + ' - Mo cua so', _on_tray_open, default=True),
        item('Tu khoi dong cung Windows',
             _on_tray_toggle_autostart,
             checked=lambda i: autostart.is_enabled()),
        pystray.Menu.SEPARATOR,
        item('Thoat', _on_tray_quit),
    )
    return pystray.Icon(APP_NAME, _get_icon_image(), APP_NAME, menu)


# ── Window close -> minimize to tray ─────────────────────────────────────────
def _on_window_closing():
    """pywebview calls this before closing. We hide instead of quitting."""
    _hide_window()
    # Returning False in pywebview 4.x cancels the close; hide() does the trick
    return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global _window, _tray_icon

    print("[app] Starting Flask...")
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    print("[app] Waiting for Flask to be ready (up to 30s)...")
    if not _wait_for_flask(timeout=30):
        print("ERROR: Flask server failed to start within 30s.")
        sys.exit(1)
    print("[app] Flask ready!")

    _tray_icon = _build_tray()
    tray_thread = threading.Thread(target=_tray_icon.run, daemon=True)
    tray_thread.start()

    _window = webview.create_window(
        title=APP_NAME,
        url=APP_URL,
        width=1150,
        height=780,
        min_size=(800, 600),
        resizable=True,
        text_select=True,
    )
    _window.events.closing += _on_window_closing

    webview.start(debug=False)
    os._exit(0)


if __name__ == '__main__':
    main()
