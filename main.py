import json
import os
import sys
import threading
import time
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

    # Start discovery beacons and listener so we can find other RoomPing Pro users on the LAN
    try:
        api.start_discovery()
    except Exception:
        pass

    # Floating always-on-top alerts window (hidden by default, can be shown from main UI and on ping)
    alerts_window = webview.create_window(
        "RoomPing Pro Alerts",
        _ALERT_INDEX,
        js_api=api,
        width=320,
        height=120,
        resizable=True,
        on_top=True,
        hidden=True,
        min_size=(160, 60),
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
        on_top=True,
    )

    def on_ping_received(sender_ip):
        # Pass IP safely to JS (no injection)
        safe_ip = json.dumps(str(sender_ip))
        window.evaluate_js(f"showAlert({safe_ip})")
        # Also surface the ping in the floating alerts window, but only if user opted in (pinned)
        try:
            if api.is_alerts_pinned():
                alerts_window.show()
                alerts_window.evaluate_js(f"showPing({safe_ip})")
        except Exception:
            pass

    # Start the UDP listener in a background thread so the window stays active
    threading.Thread(target=engine.listen_forever, args=(on_ping_received,), daemon=True).start()

    # Launch both windows, then drop the main window out of always-on-top after a short moment
    def _after_start(main_win, alerts_win):
        try:
            main_win.show()
            time.sleep(0.3)
            main_win.on_top = False
        except Exception:
            pass

    webview.start(_after_start, args=(window, alerts_window), debug=False)

if __name__ == "__main__":
    start_logic()