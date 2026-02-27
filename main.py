import json
import os
import sys
import threading
import webview
from bridge import Bridge
from logic import NetworkEngine

# Path to web UI (works when run from source or as PyInstaller .exe/.app)
if getattr(sys, "frozen", False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_WEB_INDEX = os.path.join(_BASE_DIR, "Web", "index.html")
_ALERT_INDEX = os.path.join(_BASE_DIR, "Web", "popout.html")

def start_logic():
    api = Bridge()
    engine = NetworkEngine()

    # Floating always-on-top alerts window (hidden by default, can be shown from main UI and on ping)
    alerts_window = webview.create_window(
        "RoomPing Pro Alerts",
        _ALERT_INDEX,
        js_api=api,
        width=320,
        height=140,
        resizable=True,
        on_top=True,
        hidden=True,
        frameless=True,
    )
    try:
        api.set_alerts_window(alerts_window)
    except Exception:
        # Older Bridge implementations may not support this; fail soft.
        pass

    window = webview.create_window(
        "RoomPing Pro",
        _WEB_INDEX,
        js_api=api,
        width=450,
        height=650,
    )

    def on_ping_received(sender_ip):
        # Pass IP safely to JS (no injection)
        safe_ip = json.dumps(str(sender_ip))
        window.evaluate_js(f"showAlert({safe_ip})")
        # Also surface the ping in the floating alerts window, even if the main window is minimized
        try:
            alerts_window.show()
            alerts_window.evaluate_js(f"showPing({safe_ip})")
        except Exception:
            pass

    # Start the UDP listener in a background thread so the window stays active
    threading.Thread(target=engine.listen_forever, args=(on_ping_received,), daemon=True).start()

    # Launch both windows
    webview.start(debug=False)

if __name__ == "__main__":
    start_logic()