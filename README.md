# RoomPing Pro

**Ping roommates on the same Wi‑Fi with one click.** They get an on-screen alert (and optional sound). Works on **Windows**, **macOS**, and **Linux**.

---

## Download and run (no Python required)

1. Open the **Releases** page for this repo on GitHub.
2. Download the zip for your system:
   - **Windows:** `RoomPingPro-Windows.zip` → unzip and double‑click **RoomPingPro.exe**
   - **macOS:** `RoomPingPro-macOS.zip` → unzip and open **RoomPingPro.app**
   - **Linux:** `RoomPingPro-Linux.zip` → unzip, then run `./RoomPingPro` (you may need to `chmod +x RoomPingPro` first)

No Python or other install needed. Your roommates list is stored next to the app and kept between runs.

**Windows:** If the window is blank, install [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (many PCs already have it).

### Double‑click, pin to taskbar/dock, open at startup

The downloaded app is a normal executable you can use like any other:

| What you want | Windows | macOS | Linux |
|---------------|---------|--------|--------|
| **Open the app** | Double‑click **RoomPingPro.exe** | Double‑click **RoomPingPro.app** | Run `./RoomPingPro` or double‑click it in your file manager |
| **Pin to taskbar / dock** | Right‑click the .exe → **Pin to taskbar** (or drag it to the taskbar) | Drag **RoomPingPro.app** to the Dock | Add to favorites or use the app menu (see below) |
| **Open at login / startup** | **Settings → Apps → Startup** → **Add** → browse to **RoomPingPro.exe** (or put a shortcut to it in the **Startup** folder) | **System Settings → General → Login Items** → **Add (+)** → choose **RoomPingPro.app** | Add **RoomPingPro** to **Startup Applications** (use the full path to the file, e.g. `/home/you/RoomPingPro`) |

**Linux (optional):** To get a proper app menu entry and “Add to Startup,” copy the repo file **RoomPingPro.desktop** into the same folder as the **RoomPingPro** binary, edit the file and replace `/path/to` with the real folder path, then copy the edited file to `~/.local/share/applications/`. You can then launch from the app menu and add it to Startup Applications.

---

## Run from source (if you have Python)

If you’d rather run the app from the repo (e.g. to change the code):

1. **Download** the repo (Code → Download ZIP) or clone it.
2. **Unzip** and open a terminal in the project folder.
3. **Run**
   - **Windows:** Double‑click **run.bat** or run `run.bat` in Command Prompt.
   - **Mac / Linux:** Run `chmod +x run.sh` once, then `./run.sh`.

The first run installs dependencies and creates `settings.json` for you.

**Manual run:**
```bash
pip install -r requirements.txt
python main.py
```
(Use `python3` / `pip3` on Mac/Linux if needed.)

---

## What you need

- **Same Wi‑Fi / LAN** for everyone you want to ping.
- For **built app:** nothing else (Releases include everything).
- For **source:** Python 3.7+ and, on Linux, a GUI backend:  
  `pip install pywebview[qt]`  
  (On Debian/Ubuntu you may need:  
  `sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine`)

---

## How to use

- The app shows **your** device name and MAC address. Copy your MAC and share it with roommates.
- Click **“+ Add Roommate”** and add their **name** and **MAC address**.
- Click a roommate (or PING) to send a ping. If they’re on the same network and running RoomPing Pro, they’ll get the alert.

**Optional:** Put an MP3 file named **alert.mp3** in the same folder as the app (or in `Web/assets/` when running from source) to play a sound when you receive a ping.

---

## Firewall

The app uses **UDP port 5005**. If pings don’t arrive, allow the app (or Python) through your firewall for that port.

---

## Creating new releases (for repo maintainers)

To build and publish new downloads so users don’t need Python:

1. **Create a tag** (e.g. `v1.0.0`) and push it:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. The **Build release** GitHub Action runs, builds Windows, macOS, and Linux, and **creates a Release** for that tag with the three zip files attached.
3. Users can then go to **Releases** and download the build for their OS.

To test the build without publishing: in GitHub go to **Actions → Build release → Run workflow**. When it finishes, download the zips from that run’s **Artifacts**.

To build on your own machine: from the project folder run `pip install pyinstaller && pyinstaller RoomPingPro.spec`. Output is in `dist/` (build on each OS for that OS).

---

## Project layout

| File / folder        | Purpose |
|----------------------|--------|
| `main.py`            | Entry point when running from source |
| `bridge.py`          | UI ↔ Python; creates `settings.json` on first run |
| `logic.py`           | MAC detection and network ping (all platforms) |
| `Web/`               | App UI (HTML/CSS/JS) |
| `RoomPingPro.spec`   | PyInstaller spec for building the standalone app |
| `settings.json`      | Your roommates list (created automatically; not committed) |

---

## License

Use and modify as you like. When you push to GitHub and add Releases, anyone can download and run the app on Windows, macOS, or Linux without installing Python.
