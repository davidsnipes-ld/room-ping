# RoomPing Pro

**Ping roommates on the same Wi‑Fi with one click.** They get an on-screen alert (and optional sound). Works on **Windows**, **macOS**, and **Linux**.

---

## Download and run (no Python, no terminal required)

Each release zip is **self-contained**: unzip and run. No Python, no command line, no extra install (except WebView2 on Windows if your PC doesn’t have it).

### Where to get the builds

1. Open this repo on GitHub.
2. Go to the **Releases** page:
   - Click the **Releases** link on the right side of the repo (under “About”), **or**
   - Go directly to: **`https://github.com/OWNER/REPO/releases`** (replace `OWNER` and `REPO` with this repo’s owner and name, e.g. `davidsnipes/AlertNotification`).
3. Open the **latest release** (e.g. v1.0.0).
4. In **Assets**, download the zip for your system:
   - **Windows:** `RoomPingPro-Windows.zip` → unzip and double‑click **RoomPingPro.exe**
   - **macOS:** `RoomPingPro-macOS.zip` → unzip and open **RoomPingPro.app**
   - **Linux:** **`RoomPingPro-Linux.zip`** → unzip, then **double‑click RoomPingPro** in your file manager (no terminal needed). If it won’t run, right‑click the file → **Properties** → **Permissions** → check **Allow executing as program** (or run once: `chmod +x RoomPingPro` in a terminal).

The zip files are built by GitHub Actions and appear **only on the Releases page** after the maintainer publishes a release. If there is no release yet, see [Run from source](#run-from-source-if-you-have-python) or [Creating new releases](#creating-new-releases-for-repo-maintainers).

Your roommates list is stored next to the app and kept between runs.

**Windows:** If the app window is blank, install [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (many PCs already have it).  
**Linux:** Download **RoomPingPro-Linux.zip** from the release **Assets** (not the "Code" source zip).

**macOS: App says it’s running but no window appears**  
Unzip **RoomPingPro-macOS.zip** so you have a folder with **RoomPingPro.app** inside (do not run a .pkg — the release is only the .app). Then open **Terminal** and run (replace the path with where you put the app):

```bash
/Applications/RoomPingPro.app/Contents/MacOS/RoomPingPro
```

Or if the app is in your Downloads folder:

```bash
~/Downloads/RoomPingPro.app/Contents/MacOS/RoomPingPro
```

Any error message will appear in the terminal (e.g. missing library, architecture mismatch). If you see “damaged” or Gatekeeper, right‑click the .app → **Open** → **Open** once to allow it.

### Double‑click, pin to taskbar/dock, open at startup

The downloaded app is a normal executable you can use like any other:

| What you want | Windows | macOS | Linux |
|---------------|---------|--------|--------|
| **Open the app** | Double‑click **RoomPingPro.exe** | Double‑click **RoomPingPro.app** | Double‑click **RoomPingPro** in your file manager (or open it from there) |
| **Pin to taskbar / dock** | Right‑click the .exe → **Pin to taskbar** (or drag to taskbar) | Drag **RoomPingPro.app** to the Dock | Pin the folder or add to favorites in your file manager |
| **Open at login / startup** | **Settings → Apps → Startup** → Add **RoomPingPro.exe** (or put a shortcut in the **Startup** folder) | **System Settings → General → Login Items** → **Add (+)** → choose **RoomPingPro.app** | **Startup Applications** → Add and use the full path to **RoomPingPro** (e.g. `/home/you/Downloads/RoomPingPro`) |

**Linux (optional):** For an app menu entry and easier “Add to Startup,” copy **RoomPingPro.desktop** from the repo into the same folder as **RoomPingPro**, edit the file and replace `/path/to` with that folder's path, then copy the edited file to `~/.local/share/applications/`. You can then launch from the app menu.

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

## Troubleshooting: can't see each other or send pings?

**How it works (the "goal post"):**
- The app **resolves roommate IP from their MAC** on your machine: it scans the network (broadcast + ARP, then pings each IP in your subnet) to fill the ARP table, then looks up their MAC. So **you** must be on a network where their device can be discovered (same subnet).
- The app shows **Your IP** and **We scan: …** in the profile so both people can check: if one is `192.168.1.x` and the other `192.168.0.x`, they're on different subnets and won't see each other.
- **Sender** finds receiver's IP from MAC, then sends UDP to that IP on port 5005. **Receiver** must be running the app (listening on port 5005) and allow inbound UDP 5005 in the firewall.

**Checklist:**
1. **Same WiFi / same subnet** – Check "Your IP" and "We scan" on both devices; they should be in the same range (e.g. both 192.168.1.x).
2. **MAC is correct** – Roommate is added by MAC; one wrong character and we never find them. They can copy their MAC from their app.
3. **Receiver app is open** – The app must be running to listen for pings.
4. **Firewall** – Receiver: allow RoomPingPro (or Python) for **Private** networks, or allow **inbound UDP 5005**. Sender: usually fine; some networks block ping/ARP (we try multiple subnets).
5. **Refresh** – Use the refresh button to rescan; the first scan can take a few seconds.

---

## Firewall

The app uses **UDP ports 5005** (ping), **5006** (discovery), and **5007** (messaging). Allow RoomPingPro (or Python) for **Private** networks, or allow inbound UDP 5005, 5006, and 5007. If the other person is never found or never gets the ping (e.g. on Windows), they should allow the app in Windows Security → Firewall → Allow an app for Private networks. The first ping can take a few seconds. 
---

## Creating new releases (for repo maintainers)

**End users** only download a zip from Releases and double‑click; they never run these steps. The following is for **maintainers** who build and publish the app.

To build and publish new downloads so users don’t need Python:

1. **Create a tag** (e.g. `v1.0.0`) and push it:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. The **Build release** GitHub Action runs, builds Windows, macOS, and Linux, and **creates a Release** for that tag with the three zip files attached.
3. Users can then go to **Releases** and download the build for their OS.

To test the build without publishing: in GitHub go to **Actions → Build release → Run workflow**. When it finishes, download the zips from that run’s **Artifacts**.

To build on your own machine:
- **Windows:** Double‑click **build-windows.bat** or run it in Command Prompt. Output: **dist\\RoomPingPro.exe**  
  If you get "Access is denied" or "Could not install packages", the script uses a user install (no admin). If it still fails, close other programs using Python, or run Command Prompt as Administrator, or use a venv: `python -m venv venv` then `venv\\Scripts\\activate` then `pip install pyinstaller -r requirements.txt` and `python -m PyInstaller --noconfirm RoomPingPro.spec`.
- **Linux:** Run `chmod +x build-linux.sh && ./build-linux.sh`. Output: **dist/RoomPingPro**
- **macOS:** Run **build-mac.sh** (e.g. `chmod +x build-mac.sh && ./build-mac.sh`). Output: **dist/RoomPingPro.app**

You must build on each OS to get that OS’s executable (e.g. you get RoomPingPro.exe only when building on Windows). Each output is self-contained; users unzip the release zip and double‑click to run.

**Updates:** Version uses **patch numbers**: 1.0.0 → 1.0.1 → 1.0.2. **Commit** as often as you like (no version change). When you’re ready to release, **push to main** — a pre-push hook bumps the version and commits it, then the push includes that bump. So **push** establishes the next version.  
To enable this, install the hook once: **`cp scripts/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push`** (on Windows with Git Bash: `cp scripts/pre-push .git/hooks/pre-push` then in Git Bash `chmod +x .git/hooks/pre-push`). Line 2 of `version.txt` is your GitHub repo. In the app, **Settings → Check for updates** opens the latest release page.

---

## Project layout

| File / folder        | Purpose |
|----------------------|--------|
| `main.py`            | Entry point when running from source |
| `bridge.py`          | UI ↔ Python; creates `settings.json` on first run |
| `logic.py`           | MAC detection and network ping (all platforms) |
| `Web/`               | App UI (HTML/CSS/JS); `Web/assets/` holds optional `alert.mp3` |
| `RoomPingPro.spec`   | PyInstaller spec for building the standalone app |
| `version.txt`        | Line 1: app version (1.0.1, 1.0.2…); line 2: GitHub owner/repo. Bumped automatically on push to main if hook installed |
| `bump_version.py`    | Bumps patch in version.txt (1.0.0 → 1.0.1). Used by pre-push hook; can also run manually |
| `scripts/pre-push`   | Git hook: on push to main, bumps version and commits it so push establishes the next version. Install once (see Updates above) |
| `settings.example.json` | Template; copy to `settings.json` (auto-created if missing) |
| `run.bat` / `run.sh` | One-click run from source (Windows / Mac–Linux) |
| `build-windows.bat` / `build-linux.sh` / `build-mac.sh` | Build self-contained executable on Windows / Linux / macOS (for maintainers) |
| `RoomPingPro.desktop` | Linux app menu launcher template |
| `settings.json`      | Your roommates list (created automatically; in `.gitignore`) |

**Dependencies:** The only required package is **pywebview** (`requirements.txt`). It pulls in one platform-specific dependency (e.g. WebView2 support on Windows, Qt/GTK on Linux) so the app can show a window—those are needed and kept minimal. The built `.exe`/`.app` size is mostly Python + pywebview; we exclude unused stdlib (tests, tkinter, etc.) in the spec to keep the bundle smaller.

---

## License

Use and modify as you like. When you push to GitHub and add Releases, anyone can download and run the app on Windows, macOS, or Linux without installing Python.
