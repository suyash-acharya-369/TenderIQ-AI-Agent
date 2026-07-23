// TenderIQ AI Master App Controller - Layout Preserving Engine
document.addEventListener("DOMContentLoaded", () => {
    bindSidebarNavigation();
    injectSettingsModal();
});

function bindSidebarNavigation() {
    // Dynamically map existing Stitch sidebar links across all templates without altering DOM layout
    const navLinks = document.querySelectorAll("aside a, nav a, header a, [role='navigation'] a, .sidebar a");
    console.log(`[TenderIQ Navigation] Binding ${navLinks.length} navigation links.`);
    
    navLinks.forEach(link => {
        const text = link.textContent.trim().toLowerCase();
        
        if (text.includes("dashboard")) {
            link.setAttribute("href", "/");
        } else if (text.includes("tender intelligence") || text.includes("opportunities")) {
            link.setAttribute("href", "/opportunities");
        } else if (text.includes("organizations") || text.includes("sources") || text.includes("source manager")) {
            link.setAttribute("href", "/sources");
        } else if (text.includes("keywords") || text.includes("keyword manager") || text.includes("reports")) {
            link.setAttribute("href", "/keywords");
        } else if (text.includes("ai analysis")) {
            link.setAttribute("href", "/ai-analysis");
        } else if (text.includes("settings")) {
            link.setAttribute("href", "javascript:void(0)");
            link.onclick = (e) => { 
                e.preventDefault(); 
                openSettingsModal(); 
            };
        }
    });
}


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
                    Admin System Settings
                </h2>

                <form id="settings-form" class="space-y-md" onsubmit="saveSettings(event)">
                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">OpenAI API Key</label>
                        <input type="password" id="input-openai-key" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="sk-..." />
                    </div>

                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">SMTP Host</label>
                        <input type="text" id="input-smtp-host" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="smtp.sendgrid.net" />
                    </div>

                    <div class="grid grid-cols-2 gap-md">
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">SMTP Port</label>
                            <input type="number" id="input-smtp-port" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="587" />
                        </div>
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Sender Email</label>
                            <input type="email" id="input-sender-email" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="notifications@company.com" />
                        </div>
                    </div>

                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">Meta WhatsApp Access Token</label>
                        <input type="password" id="input-wa-token" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="EAAG..." />
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
    fetch("/api/v1/settings").then(r => r.json()).then(data => {
        if (data.smtp_host) document.getElementById("input-smtp-host").value = data.smtp_host;
        if (data.smtp_port) document.getElementById("input-smtp-port").value = data.smtp_port;
        if (data.sender_email) document.getElementById("input-sender-email").value = data.sender_email;
    });
}

function closeSettingsModal() {
    const modal = document.getElementById("settings-modal");
    if (modal) modal.classList.add("hidden");
}

async function saveSettings(e) {
    e.preventDefault();
    const payload = {
        openai_api_key: document.getElementById("input-openai-key").value || undefined,
        smtp_host: document.getElementById("input-smtp-host").value || undefined,
        smtp_port: parseInt(document.getElementById("input-smtp-port").value) || undefined,
        sender_email: document.getElementById("input-sender-email").value || undefined,
        whatsapp_access_token: document.getElementById("input-wa-token").value || undefined
    };

    const res = await fetch("/api/v1/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Settings saved successfully!");
        closeSettingsModal();
    }
}
