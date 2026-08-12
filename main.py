#!/usr/bin/env python3
"""
Drive Share Manager — Entry Point (Flask web server)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def main():
    import threading
    import webbrowser
    from server import app

    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open('http://localhost:5001')

    threading.Thread(target=open_browser, daemon=True).start()

    print("╔══════════════════════════════════════════╗")
    print("║    🗂️  Drive Share Manager               ║")
    print("║    http://localhost:5001                 ║")
    print("║    Nhấn Ctrl+C để tắt                   ║")
    print("╚══════════════════════════════════════════╝")

    app.run(host='localhost', port=5001, debug=False, use_reloader=False, threaded=True)


if __name__ == '__main__':
    main()
