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

def start_logic():
    api = Bridge()
    api.start_discovery()
    engine = NetworkEngine()

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

    # 4. Start the "Ear" in a background thread so the window stays active
    threading.Thread(target=engine.listen_forever, args=(on_ping_received,), daemon=True).start()

    # 5. Launch the App
    webview.start(debug=False)

if __name__ == "__main__":
    start_logic()