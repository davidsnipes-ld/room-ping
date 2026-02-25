import socket
import threading
import tkinter as tk
from pynput import keyboard
import queue
import os
import subprocess
import re
import time
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
    """Refreshes the network list and finds the IP for a given MAC address."""
    try:
        # Check if it's YOUR MAC first
        my_mac_raw = subprocess.check_output(["networksetup", "-getmacaddress", "en0"]).decode("utf-8")
        my_mac = re.search(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", my_mac_raw).group(0)
        
        if target_mac.lower() == my_mac.lower():
            return "127.0.0.1"
    except:
        pass

    try:
        # Wake up devices on 192.168.0.x
        subprocess.Popen(["ping", "-c", "1", "192.168.0.255"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.7) 

        output = subprocess.check_output(["arp", "-an"]).decode("utf-8")
        for line in output.split('\n'):
            if target_mac.lower() in line.lower():
                ip_match = re.search(r'\((.*?)\)', line)
                if ip_match:
                    return ip_match.group(1)
    except Exception as e:
        print(f"Discovery Error: {e}")
    return None

def listen_for_pings():
    """Background thread that captures incoming PING packets."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', PORT))
        while True:
            data, addr = s.recvfrom(1024)
            if data == b"PING":
                msg_queue.put(addr[0]) # Add the IP to the queue

def check_queue(root):
    """Main thread checks for pings and displays the alert."""
    try:
        while True:
            sender_ip = msg_queue.get_nowait()
            name = "Someone"
            
            # 1. Handle Self-Test
            if sender_ip == "127.0.0.1":
                name = "Self-Test (David)"
            else:
                # 2. Identify the sender via ARP table
                try:
                    output = subprocess.check_output(["arp", "-an"]).decode("utf-8")
                    for line in output.split('\n'):
                        if sender_ip in line:
                            for combo, info in HOTKEYS_MAP.items():
                                if info[0].lower() in line.lower():
                                    name = info[1]
                                    break
                except:
                    pass
            
            log_ping(name)
            show_alert(name)
    except queue.Empty:
        pass
    root.after(100, lambda: check_queue(root))

def show_alert(name):
    """Displays the popup and plays audio."""
    #os.system(f'say "{name} is calling you"') 
    
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
    tk.Label(frame, text=f"{name} needs you right now.", font=("Arial", 20), fg="black", bg="white").pack(pady=10)
    
    tk.Button(frame, text="I'M ON IT", command=alert.destroy, font=("Arial", 16, "bold"), 
              bg="red", fg="black", width=12, height=2).pack(pady=15)

def send_ping(target_mac, name):
    print(f"DEBUG: Looking for {name}...")
    target_ip = get_ip_from_mac(target_mac)
    
    if not target_ip:
        print(f"FAILURE: Could not find {name}. Is the device awake?")
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(b"PING", (target_ip, PORT))
            print(f"SUCCESS: Ping sent to {name} at {target_ip}")
    except Exception as e:
        print(f"Network Error: {e}")

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("--- Attention Software Log Started ---\n")

    # Start Listener
    threading.Thread(target=listen_for_pings, daemon=True).start()

    root = tk.Tk()
    root.withdraw() 
    
    # Hotkeys
    def create_ping_func(mac, name):
        return lambda: send_ping(mac, name)

    bindings = {key: create_ping_func(val[0], val[1]) for key, val in HOTKEYS_MAP.items()}
    hotkey_listener = keyboard.GlobalHotKeys(bindings)
    threading.Thread(target=hotkey_listener.start, daemon=True).start()

    root.after(100, lambda: check_queue(root))
    
    print("Room Attention Software: ACTIVE")
    root.mainloop()