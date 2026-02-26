import json
import os
import re
import shutil
import socket
import sys
import urllib.request
import webbrowser
from logic import NetworkEngine, DEFAULT_PORT

def _project_dir():
    """Project root when running from source; exe/app folder when built (so settings persist)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _version_file_path():
    """Path to version.txt (in MEIPASS when frozen, else project dir)."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "version.txt")
    return os.path.join(_project_dir(), "version.txt")

def _read_version_info():
    """Return (version_string, repo_string). Repo may be empty."""
    path = _version_file_path()
    version, repo = "0.0.0", ""
    if os.path.isfile(path):
        try:
            with open(path) as f:
                lines = [l.strip() for l in f.readlines()]
            if lines:
                version = lines[0].strip() or version
            if len(lines) > 1 and lines[1] and "GITHUB_OWNER" not in lines[1]:
                repo = lines[1].strip()
        except Exception:
            pass
    return version, repo

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

    def check_reachable(self, mac, name):
        """Return True if this MAC can be resolved on the network (online), False otherwise."""
        result = self.get_reachability_and_ip(mac, name)
        return result["reachable"]

    def get_reachability_and_ip(self, mac, name):
        """Run one network scan; return reachable (bool) and ip (str or None). Used for status + IP display."""
        if not mac:
            return {"reachable": False, "ip": None}
        my_mac = self.engine.get_my_mac().lower()
        mac_clean = mac.lower().replace("-", ":")
        if mac_clean == my_mac or (name and name.lower() in socket.gethostname().lower()):
            return {"reachable": True, "ip": "127.0.0.1"}
        ip = self.engine.scan_network(mac, name or "")
        return {"reachable": ip is not None, "ip": ip}

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
            settings['users'] = [u for u in settings['users'] if u['mac'] != mac]
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        return {"status": "success"}

    def get_app_version(self):
        """Return current version and GitHub repo (for update check)."""
        version, repo = _read_version_info()
        return {"version": version, "repo": repo}

    def check_for_updates(self):
        """If repo is set, fetch latest release from GitHub. Return update info or error."""
        version, repo = _read_version_info()
        if not repo or "GITHUB_OWNER" in repo or "/" not in repo:
            return {"update_available": False, "error": "Repo not configured"}
        try:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "").lstrip("v")
            html_url = data.get("html_url", "")
            # Simple compare: strip to digits/dots
            def norm(v):
                return [int(x) for x in re.sub(r"[^0-9.]", "", v).split(".") if x]
            try:
                update_available = norm(tag) > norm(version)
            except Exception:
                update_available = tag != version
            return {
                "update_available": update_available,
                "current": version,
                "latest": tag,
                "url": html_url,
            }
        except Exception as e:
            return {"update_available": False, "error": str(e)}

    def open_url(self, url):
        """Open a URL in the default browser."""
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False