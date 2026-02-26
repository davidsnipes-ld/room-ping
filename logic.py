"""
Network discovery and UDP ping listen/send. Cross-platform: Windows, macOS, Linux.
"""
import os
import platform
import re
import shutil
import socket
import subprocess
import time
import uuid

# Shared port for UDP pings (must match in bridge.py when sending)
DEFAULT_PORT = 5005
MAC_PATTERN = re.compile(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})")


def _mac_from_uuid():
    """Fallback: format uuid.getnode() as MAC (colon-separated)."""
    node = uuid.getnode()
    return ":".join(
        "{:02x}".format((node >> (8 * (5 - i))) & 0xFF) for i in range(6)
    )


class NetworkEngine:
    def __init__(self, port=None):
        self.port = port if port is not None else DEFAULT_PORT
        self._os = platform.system()

    def get_my_mac(self):
        """Detect this machine's MAC address. Works on Windows, macOS, and Linux."""
        try:
            # --- macOS ---
            if self._os == "Darwin":
                for interface in ("en0", "en1", "eth0"):
                    try:
                        out = subprocess.check_output(
                            ["networksetup", "-getmacaddress", interface],
                            stderr=subprocess.DEVNULL,
                            timeout=2,
                        ).decode()
                        m = MAC_PATTERN.search(out)
                        if m:
                            return m.group(0).lower().replace("-", ":")
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue

            # --- Windows ---
            if self._os == "Windows":
                for cmd in (
                    ["getmac", "/fo", "csv", "/nh"],
                    ["wmic", "nic", "get", "macaddress", "/format:list"],
                ):
                    try:
                        out = subprocess.check_output(
                            cmd,
                            stderr=subprocess.DEVNULL,
                            timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                        ).decode(errors="ignore")
                        for line in out.splitlines():
                            m = MAC_PATTERN.search(line)
                            if m:
                                mac = m.group(0).lower().replace("-", ":")
                                if mac != "00:00:00:00:00:00":
                                    return mac
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue

            # --- Linux ---
            if self._os == "Linux":
                sys_net = "/sys/class/net"
                if os.path.isdir(sys_net):
                    for name in sorted(os.listdir(sys_net)):
                        if name == "lo":
                            continue
                        addr_path = os.path.join(sys_net, name, "address")
                        if os.path.isfile(addr_path):
                            try:
                                with open(addr_path) as f:
                                    mac = f.read().strip().lower().replace("-", ":")
                                if MAC_PATTERN.match(mac) and mac != "00:00:00:00:00:00":
                                    return mac
                            except OSError:
                                continue
                # ip link show (alternative)
                try:
                    out = subprocess.check_output(
                        ["ip", "link", "show"],
                        stderr=subprocess.DEVNULL,
                        timeout=2,
                    ).decode()
                    for line in out.splitlines():
                        if "link/ether" in line:
                            m = MAC_PATTERN.search(line)
                            if m:
                                return m.group(0).lower().replace("-", ":")
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass

            return _mac_from_uuid()
        except Exception as e:
            print(f"MAC discovery error: {e}")
            return _mac_from_uuid()

    def get_my_network_info(self):
        """Return this machine's IP(s) and subnet(s) we scan (including neighbor subnets for cross-subnet discovery)."""
        try:
            local_ips = socket.gethostbyname_ex(socket.gethostname())[2]
        except socket.gaierror:
            return {"ips": [], "subnets": [], "port": self.port}
        ips = [ip for ip in local_ips if not ip.startswith("127.") and len(ip.split(".")) == 4]
        seen = set()
        subnets = []
        for ip in ips:
            parts = ip.split(".")
            prefix = ".".join(parts[:-1]) + ".x"
            if prefix not in seen:
                seen.add(prefix)
                subnets.append(prefix)
            try:
                third = int(parts[2])
                for delta in (1, -1):
                    neighbor = third + delta
                    if 0 <= neighbor <= 255:
                        neighbor_x = f"{parts[0]}.{parts[1]}.{neighbor}.x"
                        if neighbor_x not in seen:
                            seen.add(neighbor_x)
                            subnets.append(neighbor_x)
            except (ValueError, IndexError):
                pass
        return {"ips": ips, "subnets": subnets[:6], "port": self.port}

    def _read_arp_for_mac(self, target_clean, arp_bin):
        """Run arp -a (or -an) and return IP if target MAC is in the table."""
        if self._os == "Windows":
            cmd = [arp_bin, "-a"]
        else:
            cmd = [arp_bin, "-an"]
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if self._os == "Windows" and hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        ).decode(errors="ignore")
        for line in output.split("\n"):
            if target_clean in line.lower().replace("-", ":"):
                m = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", line)
                if m:
                    return m.group(1)
        return None

    def scan_network(self, target_mac, target_name):
        """Resolve target_mac to an IP on the local LAN. MAC is only used to look up IP (ARP); returns IP address or None. No packet is ever sent to a MAC."""
        if not target_mac:
            return None
        my_mac = self.get_my_mac().lower()
        target_clean = target_mac.lower().replace("-", ":")
        if target_clean == my_mac:
            return "127.0.0.1"

        try:
            ping_bin = shutil.which("ping") or ("ping" if self._os == "Windows" else "/sbin/ping")
            arp_bin = shutil.which("arp") or ("arp" if self._os == "Windows" else "/usr/sbin/arp")

            try:
                local_ips = socket.gethostbyname_ex(socket.gethostname())[2]
            except socket.gaierror:
                return None

            ping_count = "-n" if self._os == "Windows" else "-c"
            creationflags = subprocess.CREATE_NO_WINDOW if self._os == "Windows" and hasattr(subprocess, "CREATE_NO_WINDOW") else 0

            # Pass 1: broadcast ping, then read ARP (fast but Windows often doesn't reply to broadcast)
            for ip in local_ips:
                if ip.startswith("127."):
                    continue
                parts = ip.split(".")
                if len(parts) != 4:
                    continue
                broadcast = ".".join(parts[:-1]) + ".255"
                subprocess.Popen(
                    [ping_bin, ping_count, "1", broadcast],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
            time.sleep(1.0)
            found = self._read_arp_for_mac(target_clean, arp_bin)
            if found:
                return found

            # Pass 2: ping each IP in each local subnet + neighbor subnets (e.g. 192.168.0.x and 192.168.1.x)
            # so devices on different subnets (same router, different AP) can find each other by MAC
            prefixes = []
            for ip in local_ips:
                if ip.startswith("127.") or len(ip.split(".")) != 4:
                    continue
                parts = ip.split(".")
                p = ".".join(parts[:-1]) + "."
                if p not in prefixes:
                    prefixes.append(p)
                # Add neighboring /24 subnet (e.g. 192.168.0 -> 192.168.1 and vice versa)
                try:
                    third = int(parts[2])
                    for delta in (1, -1):
                        neighbor = third + delta
                        if 0 <= neighbor <= 255:
                            neighbor_p = f"{parts[0]}.{parts[1]}.{neighbor}."
                            if neighbor_p not in prefixes:
                                prefixes.append(neighbor_p)
                except (ValueError, IndexError):
                    pass
            for subnet_prefix in prefixes[:5]:  # up to 5 subnets (own + neighbors)
                for i in range(1, 255):
                    candidate = subnet_prefix + str(i)
                    subprocess.Popen(
                        [ping_bin, ping_count, "1", candidate],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags,
                    )
                time.sleep(2.2)
                found = self._read_arp_for_mac(target_clean, arp_bin)
                if found:
                    return found
        except Exception as e:
            print(f"Scan error: {e}")
        return None

    def listen_forever(self, callback):
        """Listen for UDP PING packets; call callback(sender_ip); send PONG back so sender knows it was delivered."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.bind(("", self.port))
                print(f"Listening for pings on port {self.port}...")
                while True:
                    data, addr = s.recvfrom(1024)
                    if data == b"PING":
                        try:
                            callback(addr[0])
                        except Exception as e:
                            print(f"Ping callback error: {e}")
                        # Send PONG back to sender so they get delivery confirmation
                        try:
                            s.sendto(b"PONG", addr)
                        except Exception as e:
                            print(f"PONG send error: {e}")
            except Exception as e:
                print(f"Listener error: {e}")
