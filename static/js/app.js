// TenderIQ AI Master App Controller - Unified Layout & Global Action Engine
document.addEventListener("DOMContentLoaded", () => {
    bindSidebarNavigation();
    injectSettingsModal();
    injectUserManagementModal();
    injectGlobalToastContainer();
    bindGlobalActionButtons();
    injectNotificationSidebarLink();
    startNotificationSystem();
});

function injectNotificationSidebarLink() {
    const sidebars = document.querySelectorAll("nav ul");
    sidebars.forEach(ul => {
        // Check if it already has the link
        if (ul.innerHTML.includes("/notifications")) return;
        
        const li = document.createElement("li");
        li.innerHTML = `
        <a class="flex items-center gap-3 px-3 py-2 rounded-lg text-secondary dark:text-secondary-fixed-dim hover:text-on-surface dark:hover:text-on-surface-variant hover:bg-surface-variant dark:hover:bg-surface-container-highest transition-colors duration-200" href="/notifications">
            <span class="material-symbols-outlined" data-icon="notifications">notifications</span>
            <span class="font-body-md text-body-md">Notification Center</span>
        </a>
        `;
        ul.appendChild(li);
    });
}

// Notification Polling & WebSocket
let wsConnection = null;

function connectWebSocket() {
    // Determine WS protocol based on HTTP protocol
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    wsConnection = new WebSocket(`${protocol}//${host}/api/v1/notifications/ws`);

    wsConnection.onopen = () => {
        console.log("WebSocket connected for real-time notifications");
        // Send a dummy auth payload (mocked for now, assumes user ID 1)
        wsConnection.send(JSON.stringify({ "user_id": 1 }));
    };

    wsConnection.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === "NEW_NOTIFICATION") {
                // Instantly update badge and optionally show toast
                updateNotificationBadge(true);
                showGlobalToast(`New system event: ${data.event_type}`, "info");
                // If on notifications page, trigger a reload
                if (window.location.pathname.includes("/notifications") && typeof loadNotifications === "function") {
                    loadNotifications();
                }
            }
        } catch (e) {
            console.error("Error parsing WS message", e);
        }
    };

    wsConnection.onclose = () => {
        console.log("WebSocket disconnected, reconnecting in 5s...");
        setTimeout(connectWebSocket, 5000);
    };
}

async function fetchUnreadNotificationCount() {
    try {
        const res = await fetch("/api/v1/notifications/in-app?status=unread&limit=1");
        if (res.ok) {
            const notifs = await res.json();
            updateNotificationBadge(notifs.length > 0);
        }
    } catch(e) {}
    // Polling fallback every 5 minutes (300000 ms) instead of 1 min
    setTimeout(fetchUnreadNotificationCount, 300000);
}

function updateNotificationBadge(hasUnread) {
    const bellBtns = document.querySelectorAll("button .material-symbols-outlined");
    bellBtns.forEach(span => {
        if(span.textContent.trim() !== 'notifications' && span.getAttribute('data-icon') !== 'notifications') return;
        const btn = span.parentElement;
        btn.classList.add("relative");
        if (hasUnread) {
            let badge = btn.querySelector(".notif-badge");
            if (!badge) {
                badge = document.createElement("span");
                badge.className = "notif-badge absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-white dark:border-surface-container-lowest";
                btn.appendChild(badge);
            }
        } else {
            const badge = btn.querySelector(".notif-badge");
            if (badge) badge.remove();
        }
        
        btn.onclick = () => window.location.href = "/notifications";
    });
}

function startNotificationSystem() {
    connectWebSocket();
    fetchUnreadNotificationCount();
}

// 1. Unified Navigation Mapping & Active Route Highlight
function bindSidebarNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll("aside a, nav a, header a, [role='navigation'] a, .sidebar a");
    
    navLinks.forEach(link => {
        const text = link.textContent.trim().toLowerCase();
        
        if (text.includes("dashboard")) {
            link.setAttribute("href", "/");
            if (currentPath === "/" || currentPath.includes("dashboard")) link.classList.add("nav-link-active");
        } else if (text.includes("tender intelligence") || text.includes("opportunities")) {
            link.setAttribute("href", "/opportunities");
            if (currentPath.includes("opportunities") || currentPath.includes("opportunity-details")) link.classList.add("nav-link-active");
        } else if (text.includes("organizations") || text.includes("sources") || text.includes("source manager")) {
            link.setAttribute("href", "/sources");
            if (currentPath.includes("source")) link.classList.add("nav-link-active");
        } else if (text.includes("keywords") || text.includes("keyword manager")) {
            link.setAttribute("href", "/keywords");
            if (currentPath.includes("keyword")) link.classList.add("nav-link-active");
        } else if (text.includes("ai analysis")) {
            link.setAttribute("href", "/ai-analysis");
            if (currentPath.includes("ai-analysis")) link.classList.add("nav-link-active");
        } else if (text.includes("notifications") || text.includes("notification center")) {
            link.setAttribute("href", "/notifications");
            if (currentPath.includes("notification")) link.classList.add("nav-link-active");
        } else if (text.includes("user management") || text.includes("users")) {
            link.setAttribute("href", "javascript:void(0)");
            link.onclick = (e) => { e.preventDefault(); openUserManagementModal(); };
        } else if (text.includes("settings")) {
            link.setAttribute("href", "javascript:void(0)");
            link.onclick = (e) => { e.preventDefault(); openSettingsModal(); };
        }
    });
}

// 2. Global Toast Notification System
function injectGlobalToastContainer() {
    if (!document.getElementById("global-toast-container")) {
        const container = document.createElement("div");
        container.id = "global-toast-container";
        document.body.appendChild(container);
    }
}

function showGlobalToast(message, type = "info") {
    injectGlobalToastContainer();
    const container = document.getElementById("global-toast-container");
    const toast = document.createElement("div");
    toast.className = `global-toast toast-${type}`;
    
    const icon = type === "success" ? "check_circle" : type === "error" ? "error" : type === "warning" ? "warning" : "info";
    toast.innerHTML = `<span class="material-symbols-outlined text-lg">${icon}</span><span>${message}</span>`;
    
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(20px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// 3. Catch All Export, Refresh, and Print Buttons App-Wide
function bindGlobalActionButtons() {
    document.querySelectorAll("button, a").forEach(el => {
        const text = el.textContent.trim().toLowerCase();
        
        // Export CSV
        if (text.includes("export csv") || text.includes("download csv")) {
            el.onclick = (e) => {
                e.preventDefault();
                showGlobalToast("Downloading Tender Intelligence CSV export...", "info");
                window.location.href = "/api/v1/analytics/export/csv";
            };
        }
        // Export Excel
        else if (text.includes("export excel") || text.includes("download excel") || text.includes("xlsx")) {
            el.onclick = (e) => {
                e.preventDefault();
                showGlobalToast("Generating Tender Intelligence Excel workbook...", "info");
                window.location.href = "/api/v1/analytics/export/excel";
            };
        }
        // Export PDF Report
        else if (text.includes("export pdf") || text.includes("download pdf") || text.includes("executive report")) {
            el.onclick = (e) => {
                e.preventDefault();
                showGlobalToast("Generating Executive Intelligence PDF Report...", "info");
                window.location.href = "/api/v1/analytics/export/pdf";
            };
        }
    });
}

// 4. Admin Settings Modal
function injectSettingsModal() {
    if (document.getElementById("settings-modal")) return;
    
    const modalHtml = `
        <div id="settings-modal" class="hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-md">
            <div class="bg-surface-container-lowest max-w-xl w-full rounded-xl p-xl shadow-2xl space-y-lg relative text-on-surface">
                <button onclick="closeSettingsModal()" class="absolute top-md right-md text-outline hover:text-on-surface">
                    <span class="material-symbols-outlined text-2xl">close</span>
                </button>

                <h2 class="font-bold text-xl text-on-surface flex items-center gap-sm">
                    <span class="material-symbols-outlined text-primary">settings</span>
                    Admin Platform Settings
                </h2>

                <form id="settings-form" class="space-y-md" onsubmit="saveSettings(event)">
                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">OpenAI / OpenRouter API Key</label>
                        <input type="password" id="input-openai-key" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="sk-or-v1-..." />
                    </div>

                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">Default AI Provider</label>
                        <select id="input-default-provider" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface">
                            <option value="openai">OpenRouter / OpenAI (GPT-4o Mini)</option>
                            <option value="anthropic">Anthropic Claude 3.5</option>
                            <option value="gemini">Google Gemini 1.5</option>
                        </select>
                    </div>

                    <div class="grid grid-cols-2 gap-md">
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">SMTP Host</label>
                            <input type="text" id="input-smtp-host" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="smtp.sendgrid.net" />
                        </div>
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Sender Email</label>
                            <input type="email" id="input-sender-email" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="alerts@tenderiq.ai" />
                        </div>
                    </div>

                    <div class="border-t border-outline-variant pt-md space-y-md">
                        <h3 class="text-sm font-bold text-on-surface">My Notification Preferences</h3>
                        <div class="flex items-center gap-md">
                            <input type="checkbox" id="input-instant-alerts" class="w-4 h-4 text-primary rounded border-outline-variant" />
                            <label for="input-instant-alerts" class="text-sm text-on-surface">Receive Instant Alerts for High-Match Tenders</label>
                        </div>
                        <div class="flex items-center gap-md">
                            <input type="checkbox" id="input-daily-digest" class="w-4 h-4 text-primary rounded border-outline-variant" />
                            <label for="input-daily-digest" class="text-sm text-on-surface">Receive AI Daily Digest (Summary)</label>
                        </div>
                    </div>

                    <div class="flex justify-end gap-md pt-md border-t border-outline-variant">
                        <button type="button" onclick="closeSettingsModal()" class="px-md py-sm bg-surface-container-high font-semibold text-sm rounded-lg">Cancel</button>
                        <button type="submit" class="px-md py-sm bg-primary text-on-primary font-semibold text-sm rounded-lg hover:bg-surface-tint">Save Configurations</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML("beforeend", modalHtml);
}

function openSettingsModal() {
    const modal = document.getElementById("settings-modal");
    if (modal) modal.classList.remove("hidden");
    
    // Fetch global settings
    fetch("/api/v1/settings").then(r => r.json()).then(data => {
        if (data.smtp_host) document.getElementById("input-smtp-host").value = data.smtp_host;
        if (data.sender_email) document.getElementById("input-sender-email").value = data.sender_email;
        if (data.default_ai_provider) document.getElementById("input-default-provider").value = data.default_ai_provider;
    }).catch(() => {});
    
    // Fetch user preferences (mocked via standard auth user data for now, ideally an API call)
    // In our app, let's just make a quick call if we want or assume defaults. We'll leave it checked by default.
    document.getElementById("input-instant-alerts").checked = true;
    document.getElementById("input-daily-digest").checked = true;
}

function closeSettingsModal() {
    const modal = document.getElementById("settings-modal");
    if (modal) modal.classList.add("hidden");
}

async function saveSettings(e) {
    e.preventDefault();
    const payload = {
        openai_api_key: document.getElementById("input-openai-key").value || undefined,
        default_ai_provider: document.getElementById("input-default-provider").value,
        smtp_host: document.getElementById("input-smtp-host").value || undefined,
        sender_email: document.getElementById("input-sender-email").value || undefined
    };

    const res = await fetch("/api/v1/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    // Save preferences
    const prefs = {
        instant_alerts_enabled: document.getElementById("input-instant-alerts").checked,
        daily_digest_enabled: document.getElementById("input-daily-digest").checked
    };
    
    await fetch("/api/v1/users/me/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preferences: prefs })
    }).catch(() => {});

    if (res.ok) {
        showGlobalToast("Platform settings & preferences updated!", "success");
        closeSettingsModal();
    } else {
        showGlobalToast("Failed to save settings.", "error");
    }
}

// 5. Admin User Management Modal
function injectUserManagementModal() {
    if (document.getElementById("user-mgmt-modal")) return;
    
    const modalHtml = `
        <div id="user-mgmt-modal" class="hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-md">
            <div class="bg-surface-container-lowest max-w-2xl w-full max-h-[85vh] overflow-y-auto rounded-xl p-xl shadow-2xl space-y-lg relative text-on-surface">
                <button onclick="closeUserManagementModal()" class="absolute top-md right-md text-outline hover:text-on-surface">
                    <span class="material-symbols-outlined text-2xl">close</span>
                </button>

                <h2 class="font-bold text-xl text-on-surface flex items-center gap-sm">
                    <span class="material-symbols-outlined text-primary">manage_accounts</span>
                    Platform User Management
                </h2>

                <div id="users-list-container" class="space-y-sm text-xs max-h-60 overflow-y-auto border border-outline-variant/30 rounded-lg p-sm">
                    <p class="text-secondary">Loading users list...</p>
                </div>

                <form id="create-user-form" class="space-y-md border-t border-outline-variant pt-md" onsubmit="createUser(event)">
                    <h3 class="font-bold text-sm text-on-surface">Create New User</h3>
                    <div class="grid grid-cols-2 gap-md">
                        <input type="text" id="new-user-name" required placeholder="Full Name" class="p-sm border border-outline-variant rounded-lg text-sm bg-surface" />
                        <input type="email" id="new-user-email" required placeholder="Work Email" class="p-sm border border-outline-variant rounded-lg text-sm bg-surface" />
                    </div>
                    <div class="grid grid-cols-2 gap-md">
                        <input type="password" id="new-user-pass" required placeholder="Password" class="p-sm border border-outline-variant rounded-lg text-sm bg-surface" />
                        <select id="new-user-role" class="p-sm border border-outline-variant rounded-lg text-sm bg-surface">
                            <option value="Viewer">Viewer</option>
                            <option value="Manager">Manager</option>
                            <option value="Administrator">Administrator</option>
                        </select>
                    </div>
                    <div class="flex justify-end gap-md">
                        <button type="submit" class="px-md py-sm bg-primary text-on-primary font-semibold text-sm rounded-lg hover:bg-surface-tint">Create Account</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML("beforeend", modalHtml);
}

function openUserManagementModal() {
    const modal = document.getElementById("user-mgmt-modal");
    if (modal) modal.classList.remove("hidden");
    loadUsersList();
}

function closeUserManagementModal() {
    const modal = document.getElementById("user-mgmt-modal");
    if (modal) modal.classList.add("hidden");
}

async function loadUsersList() {
    const container = document.getElementById("users-list-container");
    if (!container) return;
    try {
        const res = await fetch("/api/v1/users");
        if (res.ok) {
            const users = await res.json();
            container.innerHTML = users.map(u => `
                <div class="flex items-center justify-between p-xs bg-surface-container rounded font-medium">
                    <div>
                        <span class="font-bold text-on-surface">${u.full_name}</span> (${u.email})
                    </div>
                    <div class="flex items-center gap-xs">
                        <span class="px-2 py-0.5 bg-purple-100 text-purple-700 font-bold rounded text-[10px]">${u.role}</span>
                    </div>
                </div>
            `).join("");
        } else {
            container.innerHTML = `<p class="text-red-600">Requires Administrator role to view users.</p>`;
        }
    } catch (e) {
        container.innerHTML = `<p class="text-red-600">Error loading users list.</p>`;
    }
}

async function createUser(e) {
    e.preventDefault();
    const payload = {
        full_name: document.getElementById("new-user-name").value.trim(),
        email: document.getElementById("new-user-email").value.trim(),
        password: document.getElementById("new-user-pass").value.trim(),
        role: document.getElementById("new-user-role").value
    };

    const res = await fetch("/api/v1/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        showGlobalToast(`User account created for ${payload.email}`, "success");
        document.getElementById("create-user-form").reset();
        loadUsersList();
    } else {
        const err = await res.json();
        showGlobalToast(`Failed: ${err.detail || 'Error creating user'}`, "error");
    }
}
