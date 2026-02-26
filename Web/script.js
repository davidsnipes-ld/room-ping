// --- APP STATE ---
let audioEnabled = true;

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
}

// --- INITIALIZATION ---
window.addEventListener('pywebviewready', initApp);

async function initApp() {
    console.log('Bridge found! Starting initialization...');
    try {
        if (localStorage.getItem('roomping-firewall-banner-dismissed') === '1') {
            const b = document.getElementById('firewall-banner');
            if (b) b.style.display = 'none';
        }
    } catch (e) {}
    await fetchProfile(0);
    await loadFriends();
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
                console.log("Profile Loaded:", info.name);
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
        const card = Array.from(document.querySelectorAll('.card')).find(c => c.dataset.mac === mac);
        const logEl = card ? card.querySelector('.card-log') : null;
        if (result && result.diagnostic && logEl) {
            logEl.textContent = result.diagnostic;
            logEl.className = 'card-log ' + (ok ? 'card-log-ok' : 'card-log-fail');
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

    if (!name || !mac) {
        alert("Please fill in both name and MAC address.");
        return;
    }
    const result = await pywebview.api.add_user({"name": name, "mac": mac});
    if (result && result.status === 'error') {
        alert(result.message || "Could not add roommate.");
        return;
    }
    document.getElementById('new-name').value = '';
    document.getElementById('new-mac').value = '';
    closeModal();
    showToast("Added. Finding their IP on the network…", "success");
    if (window.pywebview.api.get_reachability_and_ip) {
        await pywebview.api.get_reachability_and_ip(mac, name);
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
            if (e.target.closest('.delete-btn')) return;
            pingFriend(user.mac, user.name);
        });
        const storedIp = user.ip ? ('IP: ' + user.ip) : '';
        const logText = user.last_check || 'Checking…';
        card.innerHTML = `
    <div class="status unknown" title="Checking..."></div>
    <div class="info">
        <h3>${user.name}</h3>
        <p class="card-mac">${user.mac}</p>
        <p class="card-ip" style="${storedIp ? '' : 'display:none;'}">${storedIp}</p>
        <p class="card-log" title="What happened when we looked for this device">${logText}</p>
    </div>
    <div class="card-actions">
        <button class="ping-btn" type="button">PING</button>
        <button class="delete-btn" type="button">🗑️</button>
    </div>
`;
        const statusEl = card.querySelector('.status');
        const ipEl = card.querySelector('.card-ip');
        const logEl = card.querySelector('.card-log');
        card.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteFriend(e, user.mac);
        });
        friendsList.appendChild(card);

        // Resolve reachability and IP in one scan; update status light and show IP under name
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_reachability_and_ip) {
            try {
                const result = await pywebview.api.get_reachability_and_ip(user.mac, user.name);
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
                if (logEl && logEl.parentNode && result.diagnostic) {
                    logEl.textContent = result.diagnostic;
                    logEl.className = 'card-log ' + (result.reachable ? 'card-log-ok' : 'card-log-fail');
                }
            } catch (err) {
                if (statusEl.parentNode) {
                    statusEl.className = 'status offline';
                    statusEl.title = 'Check failed';
                }
                if (ipEl) ipEl.style.display = 'none';
                if (logEl) {
                    logEl.textContent = 'Check failed: ' + (err.message || 'error');
                    logEl.className = 'card-log card-log-fail';
                }
            }
        } else {
            statusEl.className = 'status offline';
            statusEl.title = 'Unknown';
            if (ipEl) ipEl.style.display = 'none';
            if (logEl) logEl.className = 'card-log card-log-fail';
        }
    }
}

// --- UI HELPERS ---
function openModal() { document.getElementById('modal-overlay').style.display = 'flex'; }
function closeModal() { document.getElementById('modal-overlay').style.display = 'none'; }
function openSettings() { document.getElementById('settings-modal').style.display = 'flex'; }
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