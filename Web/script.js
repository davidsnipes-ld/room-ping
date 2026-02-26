// --- APP STATE ---
let audioEnabled = true;

// Attach UI click handlers as soon as DOM is ready (so Add Roommate / Settings always work)
function attachClickHandlers() {
    const byId = (id, fn) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    };
    byId('btn-add-roommate', openModal);
    byId('btn-settings', openSettings);
    byId('btn-modal-cancel', closeModal);
    byId('btn-modal-add', saveFriend);
    byId('btn-settings-close', closeSettings);
    byId('btn-test-ping', testMyPing);
    byId('btn-copy-mac', copyMyMac);
}

// --- INITIALIZATION ---
window.addEventListener('pywebviewready', initApp);

async function initApp() {
    console.log('Bridge found! Starting initialization...');
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
        const success = await pywebview.api.ping_user(mac, name);
        if (success) {
            showToast(`Ping sent to ${name}!`, "success");
        } else {
            showToast(`${name} not found. Check WiFi!`, "error");
        }
    }
}

async function saveFriend() {
    const name = document.getElementById('new-name').value;
    const mac = document.getElementById('new-mac').value;

    if (name && mac) {
        await pywebview.api.add_user({"name": name, "mac": mac});
        document.getElementById('new-name').value = '';
        document.getElementById('new-mac').value = '';
        closeModal();
        loadFriends(); 
    } else {
        alert("Please fill in both fields!");
    }
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

    users.forEach(user => {
        const card = document.createElement('div');
        card.className = 'card';
        card.addEventListener('click', (e) => {
            if (e.target.closest('.delete-btn')) return;
            pingFriend(user.mac, user.name);
        });
        card.innerHTML = `
    <div class="status online"></div>
    <div class="info">
        <h3>${user.name}</h3>
        <p>${user.mac}</p>
    </div>
    <div class="card-actions">
        <button class="ping-btn" type="button">PING</button>
        <button class="delete-btn" type="button">🗑️</button>
    </div>
`;
        card.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteFriend(e, user.mac);
        });
        friendsList.appendChild(card);
    });
}

// --- UI HELPERS ---
function openModal() { document.getElementById('modal-overlay').style.display = 'flex'; }
function closeModal() { document.getElementById('modal-overlay').style.display = 'none'; }
function openSettings() { document.getElementById('settings-modal').style.display = 'flex'; }
function closeSettings() { document.getElementById('settings-modal').style.display = 'none'; }

function toggleAudio() {
    audioEnabled = document.getElementById('audio-toggle').checked;
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