// --- APP STATE ---
let audioEnabled = true;
const consoleLogEntries = [];
const CONSOLE_ENABLED_KEY = 'roomping-console-enabled';
const DEFAULT_CONSOLE_HEIGHT = 88;
const MIN_CONSOLE_HEIGHT = 66;
const MAX_CONSOLE_HEIGHT_VH = 50;

function isConsoleEnabled() {
    try {
        return localStorage.getItem(CONSOLE_ENABLED_KEY) !== '0';
    } catch (e) {
        return true;
    }
}

function setConsoleEnabled(enabled) {
    try {
        localStorage.setItem(CONSOLE_ENABLED_KEY, enabled ? '1' : '0');
    } catch (e) {}
}

function applyConsoleEnabledUI() {
    const enabled = isConsoleEnabled();
    const btn = document.getElementById('btn-console-toggle');
    const wrap = document.getElementById('console-wrap');
    if (btn) btn.style.display = enabled ? '' : 'none';
    if (!enabled && wrap) {
        wrap.hidden = true;
    }
}

function appendDebugLog(label, message, type) {
    const time = new Date().toLocaleTimeString();
    consoleLogEntries.push({ time, label, message, type: type || 'info' });
    if (!isConsoleEnabled()) return;
    const content = document.getElementById('console-content');
    if (content) {
        const line = document.createElement('div');
        line.className = 'console-line log-' + (type === 'ok' ? 'ok' : type === 'fail' ? 'fail' : 'info');
        line.innerHTML = '<span class="console-time">[' + escapeHtml(time) + ']</span> ' +
            (label ? '<span class="console-label">[' + escapeHtml(label) + ']</span> ' : '') +
            '<span class="console-msg">' + escapeHtml(message) + '</span>';
        content.appendChild(line);
        content.scrollTop = content.scrollHeight;
    }
}

function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function clearConsoleLog() {
    consoleLogEntries.length = 0;
    const content = document.getElementById('console-content');
    if (content) content.innerHTML = '';
}

function openConsole() {
    const wrap = document.getElementById('console-wrap');
    if (wrap) wrap.hidden = false;
}

function closeConsole() {
    const wrap = document.getElementById('console-wrap');
    if (wrap) wrap.hidden = true;
}

function toggleConsole() {
    if (!isConsoleEnabled()) return;
    const wrap = document.getElementById('console-wrap');
    if (!wrap) return;
    wrap.hidden = !wrap.hidden;
}

function toggleConsoleEnabled() {
    const cb = document.getElementById('console-enabled-toggle');
    const enabled = cb ? cb.checked : false;
    setConsoleEnabled(enabled);
    applyConsoleEnabledUI();
    if (enabled) {
        const wrap = document.getElementById('console-wrap');
        if (wrap) wrap.hidden = true; // start closed; user clicks Console to open
        rerenderConsoleFromEntries();
    } else {
        const wrap = document.getElementById('console-wrap');
        if (wrap) wrap.hidden = true;
    }
}

function rerenderConsoleFromEntries() {
    const content = document.getElementById('console-content');
    if (!content || !isConsoleEnabled()) return;
    content.innerHTML = '';
    for (const e of consoleLogEntries) {
        const line = document.createElement('div');
        line.className = 'console-line log-' + (e.type === 'ok' ? 'ok' : e.type === 'fail' ? 'fail' : 'info');
        line.innerHTML = '<span class="console-time">[' + escapeHtml(e.time) + ']</span> ' +
            (e.label ? '<span class="console-label">[' + escapeHtml(e.label) + ']</span> ' : '') +
            '<span class="console-msg">' + escapeHtml(e.message) + '</span>';
        content.appendChild(line);
    }
    content.scrollTop = content.scrollHeight;
}

function openIpModal(user) {
    const overlay = document.getElementById('ip-modal');
    if (!overlay) return;
    overlay.dataset.mac = user.mac;
    overlay.dataset.name = user.name || '';
    const desc = document.getElementById('ip-modal-desc');
    if (desc) {
        const currentIp = user.ip || 'none yet (we will try to detect it)';
        desc.textContent = `${user.name} — current IP: ${currentIp}`;
    }
    const input = document.getElementById('ip-modal-ip');
    if (input) {
        input.value = user.ip || '';
    }
    overlay.style.display = 'flex';
}

function closeIpModal() {
    const overlay = document.getElementById('ip-modal');
    if (!overlay) return;
    overlay.style.display = 'none';
}

async function saveIpFromModal() {
    const overlay = document.getElementById('ip-modal');
    if (!overlay) return;
    const mac = overlay.dataset.mac;
    const name = overlay.dataset.name || '';
    const input = document.getElementById('ip-modal-ip');
    if (!input) return;
    const ip = input.value.trim();

    if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.set_user_ip) {
        alert('Editing IP is not available in this build.');
        return;
    }

    if (!ip) {
        const ok = confirm('Clear this IP and let the app try to detect it automatically from the MAC address?');
        if (!ok) return;
    }

    const result = await pywebview.api.set_user_ip(mac, ip);
    if (result && result.status === 'error') {
        alert(result.message || 'Could not update IP.');
        return;
    }

    closeIpModal();
    if (result && result.diagnostic) {
        appendDebugLog(name, result.diagnostic, 'info');
    }
    await loadFriends();
}

// Attach UI click handlers as soon as DOM is ready (so Add Roommate / Settings always work)
function attachClickHandlers() {
    const byId = (id, fn) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    };
    byId('btn-add-roommate', openModal);
    byId('btn-refresh-status', () => loadFriends());
    byId('btn-settings', openSettings);
    byId('btn-modal-cancel', closeModal);
    byId('btn-modal-add', saveFriend);
    byId('btn-settings-close', closeSettings);
    byId('btn-check-updates', checkForUpdates);
    byId('btn-test-ping', testMyPing);
    byId('btn-copy-mac', copyMyMac);
    byId('btn-dismiss-firewall', () => {
        const b = document.getElementById('firewall-banner');
        if (b) b.style.display = 'none';
        try { localStorage.setItem('roomping-firewall-banner-dismissed', '1'); } catch (e) {}
    });
    byId('btn-console-toggle', toggleConsole);
    byId('btn-console-close', closeConsole);
    byId('btn-console-clear', clearConsoleLog);
    byId('btn-ip-cancel', closeIpModal);
    byId('btn-ip-save', saveIpFromModal);
    attachConsoleResizeHandle();
}

function attachConsoleResizeHandle() {
    const handle = document.getElementById('console-resize-handle');
    const wrap = document.getElementById('console-wrap');
    if (!handle || !wrap) return;
    let startY = 0, startH = 0;
    handle.addEventListener('mousedown', function (e) {
        e.preventDefault();
        startY = e.clientY;
        startH = wrap.offsetHeight;
        const maxH = Math.min(wrap.parentElement.offsetHeight * (MAX_CONSOLE_HEIGHT_VH / 100), 400);
        function onMove(e) {
            const dy = startY - e.clientY;
            let h = Math.max(MIN_CONSOLE_HEIGHT, Math.min(maxH, startH + dy));
            wrap.style.height = h + 'px';
        }
        function onUp() {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
}

// --- INITIALIZATION ---
window.addEventListener('pywebviewready', initApp);

async function initApp() {
    try {
        if (localStorage.getItem('roomping-firewall-banner-dismissed') === '1') {
            const b = document.getElementById('firewall-banner');
            if (b) b.style.display = 'none';
        }
        const cb = document.getElementById('console-enabled-toggle');
        if (cb) cb.checked = isConsoleEnabled();
        applyConsoleEnabledUI();
    } catch (e) {}
    appendDebugLog('', 'App starting…', 'info');
    await fetchProfile(0);
    await loadFriends();
    appendDebugLog('', 'Ready. Use Console to see connection and ping details.', 'info');
}

async function fetchProfile(retries) {
    try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_my_info) {
            const info = await pywebview.api.get_my_info();
            if (info) {
                document.getElementById('my-name').innerText = info.name;
                document.getElementById('my-mac').innerText = info.mac;
                const netEl = document.getElementById('my-network');
                if (netEl && (info.ips || info.subnets)) {
                    const parts = [];
                    if (info.ips && info.ips.length) parts.push('Your IP: ' + info.ips.join(', '));
                    if (info.subnets && info.subnets.length) parts.push('We scan: ' + info.subnets.join(', '));
                    netEl.textContent = parts.join(' · ');
                    netEl.title = 'Same subnet = can find each other. Receiver must allow UDP ' + (info.port || 5005) + '.';
                }
                appendDebugLog('', 'Profile loaded: ' + info.name + ', MAC ' + info.mac, 'info');
                return;
            }
        }
    } catch (err) {
        console.error("Profile fetch error:", err);
    }

    // Retry logic if bridge isn't quite ready
    if (retries < 10) {
        console.log(`Retrying profile fetch... (${retries + 1})`);
        setTimeout(() => fetchProfile(retries + 1), 200);
    }
}

async function testMyPing() {
    const myMac = document.getElementById('my-mac').innerText;
    const myName = document.getElementById('my-name').innerText;
    
    console.log("Self-testing ping...");
    // We pass 'Self' so the bridge knows it's an internal test
    await pingFriend(myMac, myName);
}

// --- CORE ACTIONS ---
async function pingFriend(mac, name) {
    console.log(`Pinging: ${name}`);
    if (window.pywebview && window.pywebview.api) {
        const result = await pywebview.api.ping_user(mac, name);
        const ok = result && (result.success === true);
        if (result && result.diagnostic) {
            appendDebugLog(name, result.diagnostic, ok ? 'ok' : 'fail');
        }
        if (ok) {
            showToast(`Ping sent to ${name}!`, "success");
        } else {
            const msg = result && result.hint
                ? result.hint + (result.your_ip ? ' Your IP: ' + result.your_ip + '.' : '')
                : (name + ' not found. Same WiFi? Is their app open? Firewall allows UDP 5005?');
            showToast(msg, "error");
        }
    }
}

async function saveFriend() {
    const name = document.getElementById('new-name').value.trim();
    const mac = document.getElementById('new-mac').value.trim();
    const ip = document.getElementById('new-ip').value.trim();

    if (!name || !mac) {
        alert("Please fill in both name and MAC address.");
        return;
    }
    const result = await pywebview.api.add_user({"name": name, "mac": mac, "ip": ip || undefined});
    if (result && result.status === 'error') {
        alert(result.message || "Could not add roommate.");
        return;
    }
    document.getElementById('new-name').value = '';
    document.getElementById('new-mac').value = '';
    document.getElementById('new-ip').value = '';
    closeModal();
    showToast(ip ? "Added with IP. Refreshing…" : "Added. Finding their IP on the network…", "success");
    if (window.pywebview.api.get_reachability_and_ip) {
        await pywebview.api.get_reachability_and_ip(mac, name, ip || null);
    }
    await loadFriends();
}

async function deleteFriend(event, mac) {
    event.stopPropagation(); // Prevents the "Ping" from firing when clicking delete
    if (confirm("Remove this roommate?")) {
        await pywebview.api.delete_user(mac);
        loadFriends(); // Refresh the list
    }
}

async function loadFriends() {
    const friendsList = document.getElementById('friends-list');
    const settings = await pywebview.api.get_settings();
    friendsList.innerHTML = '';

    const users = settings.users || [];
    if (users.length === 0) {
        friendsList.innerHTML = '<p style="text-align:center; color:#666; margin-top:20px;">No roommates added yet.</p>';
        return;
    }

    for (const user of users) {
        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.mac = user.mac;
        card.addEventListener('click', (e) => {
            if (e.target.closest('.delete-btn') || e.target.closest('.ip-btn')) return;
            pingFriend(user.mac, user.name);
        });
        const storedIp = user.ip ? ('IP: ' + user.ip) : '';
        card.innerHTML = `
    <div class="status unknown" title="Checking..."></div>
    <div class="info">
        <h3>${user.name}</h3>
        <p class="card-mac">${user.mac}</p>
        <p class="card-ip" style="${storedIp ? '' : 'display:none;'}">${storedIp}</p>
    </div>
    <div class="card-actions">
        <button class="ping-btn" type="button">PING</button>
        <button class="ip-btn" type="button" title="View or edit the IP we have stored for this MAC">IP</button>
        <button class="delete-btn" type="button">🗑️</button>
    </div>
`;
        const statusEl = card.querySelector('.status');
        const ipEl = card.querySelector('.card-ip');
        card.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteFriend(e, user.mac);
        });
        const ipBtn = card.querySelector('.ip-btn');
        if (ipBtn) {
            ipBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openIpModal(user);
            });
        }
        friendsList.appendChild(card);

        // Resolve reachability and IP in one scan; update status light and show IP under name; log to debug panel
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_reachability_and_ip) {
            try {
                appendDebugLog(user.name, user.ip ? 'Using saved IP for ' + user.name + '…' : 'Checking network for MAC ' + user.mac + '…', 'info');
                const result = await pywebview.api.get_reachability_and_ip(user.mac, user.name, user.ip || null);
                if (statusEl.parentNode) {
                    statusEl.className = 'status ' + (result.reachable ? 'online' : 'offline');
                    statusEl.title = result.reachable
                        ? 'Online – we resolved their IP from MAC'
                        : 'Offline – could not find this MAC on the network. Same WiFi? Same subnet? Try refresh.';
                }
                if (ipEl && ipEl.parentNode) {
                    if (result.ip) {
                        ipEl.textContent = 'IP: ' + result.ip;
                        ipEl.style.display = '';
                    } else {
                        ipEl.style.display = 'none';
                    }
                }
                if (result.diagnostic) {
                    appendDebugLog(user.name, result.diagnostic, result.reachable ? 'ok' : 'fail');
                }
            } catch (err) {
                if (statusEl.parentNode) {
                    statusEl.className = 'status offline';
                    statusEl.title = 'Check failed';
                }
                if (ipEl) ipEl.style.display = 'none';
                appendDebugLog(user.name, 'Check failed: ' + (err.message || 'error'), 'fail');
            }
        } else {
            statusEl.className = 'status offline';
            statusEl.title = 'Unknown';
            if (ipEl) ipEl.style.display = 'none';
        }
    }
}

// --- UI HELPERS ---
function openModal() { document.getElementById('modal-overlay').style.display = 'flex'; }
function closeModal() { document.getElementById('modal-overlay').style.display = 'none'; }
function openSettings() {
    document.getElementById('settings-modal').style.display = 'flex';
    const cb = document.getElementById('console-enabled-toggle');
    if (cb) cb.checked = isConsoleEnabled();
}
function closeSettings() { document.getElementById('settings-modal').style.display = 'none'; }

function toggleAudio() {
    audioEnabled = document.getElementById('audio-toggle').checked;
}

async function checkForUpdates() {
    const btn = document.getElementById('btn-check-updates');
    if (btn) btn.disabled = true;
    try {
        if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.check_for_updates) {
            showToast('Update check not available.', 'error');
            return;
        }
        const result = await pywebview.api.check_for_updates();
        if (result.error) {
            showToast(result.error === 'Repo not configured' ? 'Set your GitHub repo in version.txt (line 2).' : result.error, 'error');
            return;
        }
        if (result.update_available) {
            showToast(`Update available: ${result.latest}. Opening download page...`, 'success');
            if (result.url) pywebview.api.open_url(result.url);
        } else {
            showToast(`You're on the latest version (${result.current}).`, 'success');
        }
    } catch (err) {
        showToast('Update check failed.', 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

function copyMyMac() {
    const mac = document.getElementById('my-mac').innerText;
    navigator.clipboard.writeText(mac);
    showToast("MAC copied!", "success");
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = 'ping-notification';
    if(type === "error") toast.style.background = "#555";
    toast.innerHTML = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// --- PYTHON CALLBACKS ---
window.showAlert = function(senderIp) {
    showToast(`<strong>PING!</strong> From: ${senderIp}`, "success");
    if (audioEnabled) {
        const audio = document.getElementById('ping-sound');
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(e => console.log("Audio play blocked"));
        }
    }
}

// Attach button handlers immediately so Add Roommate / Settings work in all webview environments
attachClickHandlers();

if (window.pywebview) {
    initApp();
} else {
    window.addEventListener('pywebviewready', initApp);
}