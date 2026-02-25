import sys
import subprocess
import os
import socket
import threading
import tkinter as tk
import queue
import re
import time
import platform
import shutil
import json
import uuid
from datetime import datetime

# --- AUTO-INSTALLER ---
try:
    from pynput import keyboard
except ImportError:
    print("Installing missing libraries... please wait.")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])
    from pynput import keyboard

# --- SETTINGS LOADER ---
CONFIG_FILE = "settings.json"

def get_router_ip():
    current_os = platform.system()
    try:
        if current_os == "Windows":
            process = subprocess.check_output(['route', 'print', '0.0.0.0'])
            match = re.search(r'0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)', process.decode())
            return match.group(1) if match else None
        else:
            process = subprocess.check_output(['netstat', '-rn'])
            match = re.search(r'default\s+([\d\.]+)', process.decode())
            return match.group(1) if match else None
    except:
        return None

def load_settings():
    router_id = get_router_ip()
    default_config = {
        "locked_router_ip": router_id,
        "hotkeys": {
            "<ctrl>+<alt>+1": ["68:ca:c4:97:1c:2d", "David"],
            "<ctrl>+<alt>+2": ["Z9:Y8:X7:W6:V5:U4", "Levi"],
            "<ctrl>+<alt>+3": ["00:11:22:33:44:55", "Dan"],
            "<ctrl>+<alt>+4": ["66:77:88:99:AA:BB", "Aaron"]
        }
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

SETTINGS = load_settings()
PORT = 5005
msg_queue = queue.Queue()

# --- NETWORK LOGIC ---
def get_ip_from_mac(target_mac, target_name):
    current_os = platform.system()
    
    # 1. FOOLPROOF SELF-TEST
    try:
        my_mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
        if target_mac.lower().replace('-', ':') == my_mac.lower():
            return "127.0.0.1"
        if target_name.lower() in socket.gethostname().lower():
            return "127.0.0.1"
    except:
        pass

    # 2. NETWORK DISCOVERY
    try:
        ping_bin = shutil.which("ping") or ("ping" if current_os == "Windows" else "/sbin/ping")
        arp_bin = shutil.which("arp") or ("arp" if current_os == "Windows" else "/usr/sbin/arp")
        
        router_ip = get_router_ip()
        if not router_ip: return None
            
        broadcast = ".".join(router_ip.split('.')[:-1]) + ".255"
        flag = "-n" if current_os == "Windows" else "-c"
        
        subprocess.Popen([ping_bin, flag, "1", broadcast], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.7)

        cmd = [arp_bin, "-a"] if current_os == "Windows" else [arp_bin, "-an"]
        output = subprocess.check_output(cmd).decode(errors='ignore')
        
        target_mac_clean = target_mac.lower().replace('-', ':')
        for line in output.split('\n'):
            line_clean = line.lower().replace('-', ':')
            if target_mac_clean in line_clean:
                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                if ip_match: return ip_match.group(1)
    except Exception as e:
        print(f"Discovery Error: {e}")
    return None

def show_alert(ip):
    alert = tk.Toplevel()
    alert.title("PING!")
    alert.attributes("-topmost", True)
    alert.geometry("400x200")
    
    name = "Someone"
    if ip == "127.0.0.1":
        name = "Self-Test"
    else:
        try:
            arp_bin = shutil.which("arp") or ("arp" if platform.system() == "Windows" else "/usr/sbin/arp")
            cmd = [arp_bin, "-a"] if platform.system() == "Windows" else [arp_bin, "-an"]
            output = subprocess.check_output(cmd).decode(errors='ignore')
            for line in output.split('\n'):
                if ip in line:
                    for key, info in SETTINGS["hotkeys"].items():
                        if info[0].lower().replace('-', ':') in line.lower().replace('-', ':'):
                            name = info[1]
        except: pass

    tk.Label(alert, text=f"PING FROM: {name}", font=("Arial", 16, "bold"), fg="red").pack(expand=True)
    tk.Button(alert, text="DISMISS", command=alert.destroy, width=15, height=2).pack(pady=20)

def listen_for_pings():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', PORT))
        while True:
            data, addr = s.recvfrom(1024)
            if data == b"PING":
                msg_queue.put(addr[0])

def check_queue(root):
    try:
        while True:
            sender_ip = msg_queue.get_nowait()
            show_alert(sender_ip)
    except queue.Empty:
        pass
    root.after(100, lambda: check_queue(root))

def send_ping(target_mac, name):
    print(f"Searching for {name}...")
    target_ip = get_ip_from_mac(target_mac, name)
    if target_ip:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(b"PING", (target_ip, PORT))
            print(f"Sent to {name} ({target_ip})")
    else:
        print(f"FAILURE: {name} not found.")

if __name__ == "__main__":
    current_router = get_router_ip()
    threading.Thread(target=listen_for_pings, daemon=True).start()
    
    root = tk.Tk()
    root.withdraw()

    def create_ping_func(mac, name): return lambda: send_ping(mac, name)
    bindings = {k: create_ping_func(v[0], v[1]) for k, v in SETTINGS["hotkeys"].items()}
    
    listener = keyboard.GlobalHotKeys(bindings)
    threading.Thread(target=listener.start, daemon=True).start()
    
    root.after(100, lambda: check_queue(root))
    print(f"Room Ping ACTIVE | Your Hostname: {socket.gethostname()}")
    root.mainloop()