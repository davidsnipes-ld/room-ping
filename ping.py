import socket
import threading
import tkinter as tk
from pynput import keyboard
import queue
import os
import subprocess
import re
import time
import platform
import shutil
from datetime import datetime

# --- CONFIGURATION ---
HOTKEYS_MAP = {
    '<ctrl>+<alt>+1': ('68:ca:c4:97:1c:2d', 'David'),
    '<ctrl>+<alt>+2': ('Z9:Y8:X7:W6:V5:U4', 'Levi'),
    '<ctrl>+<alt>+3': ('00:11:22:33:44:55', 'Dan'),
    '<ctrl>+<alt>+4': ('66:77:88:99:AA:BB', 'Aaron'),
}
PORT = 5005
LOG_FILE = "ping_log.txt"
msg_queue = queue.Queue()
# ---------------------

def log_ping(name):
    """Appends the ping event to a local text file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {name} requested attention.\n")

def get_ip_from_mac(target_mac):
    current_os = platform.system()
    
    # 1. Self-Test Check (Mac Only)
    try:
        if current_os == "Darwin": 
            my_mac_raw = subprocess.check_output(["networksetup", "-getmacaddress", "en0"]).decode()
            if target_mac.lower() in my_mac_raw.lower(): return "127.0.0.1"
    except: pass

    # 2. Network Discovery
    try:
        ping_bin = shutil.which("ping")
        arp_bin = shutil.which("arp")
        
        # Wake up network - broadcast address
        broadcast = "192.168.0.255"
        if current_os == "Windows":
            subprocess.Popen([ping_bin, "-n", "1", broadcast], stdout=subprocess.DEVNULL)
        else:
            subprocess.Popen([ping_bin, "-c", "1", broadcast], stdout=subprocess.DEVNULL)
        
        time.sleep(0.7)

        # Get ARP table based on OS
        cmd = [arp_bin, "-a"] if current_os == "Windows" else [arp_bin, "-an"]
        output = subprocess.check_output(cmd).decode(errors='ignore')
        
        # Clean MACs to handle Windows dashes (-) vs Unix colons (:)
        target_mac_clean = target_mac.lower().replace('-', ':')
        
        for line in output.split('\n'):
            line_clean = line.lower().replace('-', ':')
            if target_mac_clean in line_clean:
                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                if ip_match: return ip_match.group(1)
    except Exception as e:
        print(f"Discovery Error: {e}")
    return None

def listen_for_pings():
    """Background thread to catch incoming UDP packets."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', PORT))
        while True:
            data, addr = s.recvfrom(1024)
            if data == b"PING":
                msg_queue.put(addr[0])

def check_queue(root):
    """Main thread checks for pings and shows the alert."""
    try:
        while True:
            sender_ip = msg_queue.get_nowait()
            name = "Someone"
            
            if sender_ip == "127.0.0.1":
                name = "Self-Test"
            else:
                try:
                    arp_bin = shutil.which("arp")
                    cmd = [arp_bin, "-a"] if platform.system() == "Windows" else [arp_bin, "-an"]
                    output = subprocess.check_output(cmd).decode(errors='ignore')
                    for line in output.split('\n'):
                        if sender_ip in line:
                            for combo, info in HOTKEYS_MAP.items():
                                mac_clean = info[0].lower().replace('-', ':')
                                if mac_clean in line.lower().replace('-', ':'):
                                    name = info[1]
                                    break
                except: pass
            
            log_ping(name)
            show_alert(name)
    except queue.Empty:
        pass
    root.after(100, lambda: check_queue(root))

def show_alert(name):
    """The centered popup window."""
    alert = tk.Toplevel() 
    alert.title("PING!")
    alert.attributes("-topmost", True)
    
    width, height = 500, 260
    x = (alert.winfo_screenwidth() // 2) - (width // 2)
    y = (alert.winfo_screenheight() // 2) - (height // 2)
    alert.geometry(f"{width}x{height}+{x}+{y}")
    
    frame = tk.Frame(alert, bg="white", highlightbackground="red", highlightthickness=8)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="ATTENTION!", font=("Arial", 32, "bold"), fg="red", bg="white").pack(pady=(20, 0))
    tk.Label(frame, text=f"{name} needs you.", font=("Arial", 20), fg="black", bg="white").pack(pady=10)
    tk.Button(frame, text="I'M ON IT", command=alert.destroy, font=("Arial", 16, "bold"), width=12).pack(pady=15)

def send_ping(target_mac, name):
    print(f"DEBUG: Finding {name}...")
    target_ip = get_ip_from_mac(target_mac)
    if not target_ip:
        print(f"FAILURE: {name} not found on the network.")
        return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(b"PING", (target_ip, PORT))
            print(f"SUCCESS: Ping sent to {name} at {target_ip}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("--- Attention Software Log Started ---\n")

    threading.Thread(target=listen_for_pings, daemon=True).start()
    
    root = tk.Tk()
    root.withdraw() 
    
    def create_ping_func(mac, name): return lambda: send_ping(mac, name)
    bindings = {key: create_ping_func(val[0], val[1]) for key, val in HOTKEYS_MAP.items()}
    
    hotkey_listener = keyboard.GlobalHotKeys(bindings)
    threading.Thread(target=hotkey_listener.start, daemon=True).start()
    
    root.after(100, lambda: check_queue(root))
    
    print(f"Room Attention Software: ACTIVE on {platform.system()}")
    root.mainloop()