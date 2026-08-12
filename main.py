#!/usr/bin/env python3
"""
Drive Share Manager — Entry Point (Flask web server)
"""
import sys
import os

# When bundled with PyInstaller, sys._MEIPASS contains the temp extraction dir.
# Ensure our bundled packages are importable.
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)  # type: ignore[attr-defined]
else:
    sys.path.insert(0, os.path.dirname(__file__))


def main():
    import threading
    import webbrowser
    from server import app

    # Show user where data is stored (credentials.json, token.json, config.json)
    if sys.platform == "win32":
        data_dir = os.path.join(os.environ.get("APPDATA", "~"), "GDriveCloner")
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".gdrivecloner")

    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open('http://localhost:5001')

    threading.Thread(target=open_browser, daemon=True).start()

    print("╔══════════════════════════════════════════╗")
    print("║    🗂️  Drive Share Manager               ║")
    print("║    http://localhost:5001                 ║")
    print("║    Nhấn Ctrl+C để tắt                   ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  Data dir: {data_dir[:30]:<30}  ║")
    print("╚══════════════════════════════════════════╝")

    app.run(host='localhost', port=5001, debug=False, use_reloader=False, threaded=True)


if __name__ == '__main__':
    main()

