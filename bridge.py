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

    def _mac_norm(self, mac):
        return (mac or "").lower().replace("-", ":")

    def _find_user_by_mac(self, settings, mac):
        mac_clean = self._mac_norm(mac)
        for u in settings.get("users", []):
            if self._mac_norm(u.get("mac")) == mac_clean:
                return u
        return None

    def add_user(self, user_data):
        settings = self.get_settings()
        if 'users' not in settings:
            settings['users'] = []
        settings['users'].append(dict(user_data))  # name, mac; ip filled when we resolve
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        return {"status": "success"}

    def update_user_ip(self, mac, ip):
        """Store or update the last-known IP for this MAC. MAC is only the lookup key; we hold the IP for sending pings."""
        if not mac or not ip:
            return
        settings = self.get_settings()
        user = self._find_user_by_mac(settings, mac)
        if user is not None:
            user["ip"] = ip
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=4)

    def check_reachable(self, mac, name):
        """Return True if this MAC can be resolved on the network (online), False otherwise."""
        result = self.get_reachability_and_ip(mac, name)
        return result["reachable"]

    def get_reachability_and_ip(self, mac, name):
        """Run one network scan; return reachable (bool) and ip (str or None). Saves IP when found."""
        if not mac:
            return {"reachable": False, "ip": None}
        my_mac = self.engine.get_my_mac().lower()
        mac_clean = self._mac_norm(mac)
        if mac_clean == my_mac or (name and name.lower() in socket.gethostname().lower()):
            self.update_user_ip(mac, "127.0.0.1")
            return {"reachable": True, "ip": "127.0.0.1"}
        ip = self.engine.scan_network(mac, name or "")
        if ip:
            self.update_user_ip(mac, ip)
        return {"reachable": ip is not None, "ip": ip}

    def _send_ping(self, target_ip):
        """Send the ping to an IP address only. We never send to a MAC; MAC is only used to find the IP."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(b"PING", (target_ip, DEFAULT_PORT))

    def ping_user(self, mac, name):
        """Ping is always sent to an IP. MAC is only the signal to look up (or recall) that IP. Uses stored IP if we have it, else resolves MAC → IP and saves it."""
        net = self.engine.get_my_network_info()
        my_mac = self.engine.get_my_mac().lower()
        my_hostname = socket.gethostname().lower()
        mac_clean = self._mac_norm(mac)

        if mac_clean == my_mac or (name and name.lower() in my_hostname):
            self.update_user_ip(mac, "127.0.0.1")
            try:
                self._send_ping("127.0.0.1")
                return {"success": True}
            except Exception as e:
                return {"success": False, "your_ip": "", "subnets": [], "hint": str(e)}

        settings = self.get_settings()
        user = self._find_user_by_mac(settings, mac)
        stored_ip = (user or {}).get("ip") if user else None

        # 1) Send to stored IP if we have it (ping always goes to IP, never to MAC)
        if stored_ip:
            try:
                self._send_ping(stored_ip)
                return {"success": True}
            except Exception:
                pass

        # 2) Resolve MAC → IP (MAC is only lookup key), then save IP and send ping to that IP
        target_ip = self.engine.scan_network(mac, name or "")
        if target_ip:
            self.update_user_ip(mac, target_ip)
            try:
                self._send_ping(target_ip)
                return {"success": True}
            except Exception as e:
                return {
                    "success": False,
                    "your_ip": net.get("ips", [""])[0] if net.get("ips") else "",
                    "subnets": net.get("subnets", []),
                    "hint": str(e),
                }

        return {
            "success": False,
            "your_ip": net.get("ips", [""])[0] if net.get("ips") else "",
            "subnets": net.get("subnets", []),
            "hint": "Could not resolve their IP from MAC. Same WiFi? Same subnet? Their firewall may block ping.",
        }
    
    def get_my_info(self):
        try:
            name = str(socket.gethostname())
            mac = str(self.engine.get_my_mac())
            net = self.engine.get_my_network_info()
            print(f"Sending Profile: {name} | {mac}")  # Check your terminal for this!
            return {
                "name": name,
                "mac": mac,
                "ips": net.get("ips", []),
                "subnets": net.get("subnets", []),
                "port": net.get("port", 5005),
            }
        except Exception as e:
            print(f"Profile Error: {e}")
            return {"name": "Unknown Device", "mac": "00:00:00:00:00:00", "ips": [], "subnets": [], "port": 5005}

    def get_my_network_info(self):
        """Return this machine's IP(s) and subnet(s) for diagnostics (goal post for sender/receiver)."""
        return self.engine.get_my_network_info()
    
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