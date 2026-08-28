#!/usr/bin/env python3
"""
Drive Share Manager — Tray Entry Point
Runs the Flask web server in the background and shows a system tray icon.
"""
import sys
import os
import threading
import time
import webbrowser
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
import autostart

# Ensure our bundled packages are importable (same as main.py)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(__file__))

def create_default_icon():
    """Generate a simple default icon if assets/icon.png is missing."""
    image = Image.new('RGB', (64, 64), color=(33, 150, 243))
    d = ImageDraw.Draw(image)
    # Just draw a simple 'G'
    try:
        # Try to load a default font
        font = ImageFont.load_default()
        d.text((22, 22), "G", fill=(255, 255, 255), font=font)
    except:
        pass
    return image

def get_icon_image():
    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, 'assets', 'icon.png')
    
    if os.path.exists(icon_path):
        return Image.open(icon_path)
    return create_default_icon()

def run_flask_server():
    # Import app here so we don't block
    from server import app
    # Run silently, disable Werkzeug logging if possible
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='localhost', port=5001, debug=False, use_reloader=False, threaded=True)

def on_open(icon, item):
    webbrowser.open('http://localhost:5001')

def on_toggle_autostart(icon, item):
    autostart.set_state(not autostart.is_enabled())

def on_quit(icon, item):
    icon.stop()
    os._exit(0)  # Force exit since flask is running in a daemon thread

def main():
    # 1. Start flask in background
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    # 2. Automatically open browser on start
    def auto_open():
        time.sleep(1.5)
        webbrowser.open('http://localhost:5001')
    threading.Thread(target=auto_open, daemon=True).start()

    # 3. Create Tray Icon
    image = get_icon_image()
    menu = pystray.Menu(
        item('Mở GDriveCloner', on_open, default=True),
        item('Tự khởi động cùng máy', on_toggle_autostart, checked=lambda item: autostart.is_enabled()),
        pystray.Menu.SEPARATOR,
        item('Thoát', on_quit)
    )
    
    icon = pystray.Icon("GDriveCloner", image, "GDriveCloner", menu)
    icon.run()

if __name__ == '__main__':
    main()
