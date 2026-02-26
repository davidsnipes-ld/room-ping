import json
import os
import shutil
import socket
import sys
from logic import NetworkEngine, DEFAULT_PORT

def _project_dir():
    """Project root when running from source; exe/app folder when built (so settings persist)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class Bridge:
    def __init__(self):
        self.engine = NetworkEngine()
        self.settings_file = os.path.join(_project_dir(), "settings.json")
        self._ensure_settings_exists()

    def _ensure_settings_exists(self):
        """Create settings.json from example or default on first run (plug-and-play)."""
        if os.path.exists(self.settings_file):
            return
        example = os.path.join(_project_dir(), "settings.example.json")
        if os.path.exists(example):
            shutil.copy(example, self.settings_file)
        else:
            with open(self.settings_file, "w") as f:
                json.dump({"users": []}, f, indent=4)

    def get_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                return json.load(f)
        return {"users": []}

    def add_user(self, user_data):
        settings = self.get_settings()
        if 'users' not in settings:
            settings['users'] = []
        settings['users'].append(user_data)
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        return {"status": "success"}

    def ping_user(self, mac, name):
        my_mac = self.engine.get_my_mac()
        my_hostname = socket.gethostname().lower()
        
        if mac.lower().replace('-', ':') == my_mac.lower() or name.lower() in my_hostname:
            target_ip = "127.0.0.1"
        else:
            target_ip = self.engine.scan_network(mac, name)
        
        if target_ip:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(b"PING", (target_ip, DEFAULT_PORT))
            return True
        return False
    
    def get_my_info(self):
        try:
            name = str(socket.gethostname())
            mac = str(self.engine.get_my_mac())
            print(f"Sending Profile: {name} | {mac}") # Check your terminal for this!
            return {"name": name, "mac": mac}
        except Exception as e:
            print(f"Profile Error: {e}")
            return {"name": "Unknown Device", "mac": "00:00:00:00:00:00"}
    
    def delete_user(self, mac):
        """Removes a user from settings.json by their MAC address"""
        settings = self.get_settings()
        if 'users' in settings:
            # Keep everyone EXCEPT the person with this MAC
            settings['users'] = [u for u in settings['users'] if u['mac'] != mac]
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        return {"status": "success"}