// TenderIQ AI Source Manager Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("source")) {
        loadSources();
        injectSourceModal();
        bindNewSourceButton();
    }
});

let allSources = [];

async function loadSources() {
    try {
        const res = await fetch("/api/v1/sources");
        if (res.ok) {
            allSources = await res.json();
            renderSourceList(allSources);
        }
    } catch (e) {
        console.error("Error loading sources:", e);
    }
}

function renderSourceList(sources) {
    const container = document.getElementById("sources-grid");
    if (!container) return;

    container.innerHTML = sources.map(s => {
        const isHealthy = s.status === 'active';
        const statusColor = isHealthy ? '#059669' : '#eab308';
        const syncFreq = s.frequency || 'Daily';
        
        return `
            <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg flex flex-col shadow-[0px_4px_12px_rgba(15,23,42,0.03)] hover:shadow-md transition-shadow">
                <div class="flex justify-between items-start mb-md">
                    <div class="flex items-center gap-md">
                        <div class="w-12 h-12 rounded bg-surface border border-outline-variant flex items-center justify-center p-xs text-secondary overflow-hidden">
                            <span class="material-symbols-outlined text-3xl">public</span>
                        </div>
                        <div>
                            <h4 class="font-headline-sm text-headline-sm font-semibold leading-tight max-w-[200px] truncate" title="${s.name}">${s.name}</h4>
                            <span class="font-label-sm text-label-sm text-secondary">${s.country} / ${s.category}</span>
                        </div>
                    </div>
                    <div class="w-3 h-3 rounded-full shadow-sm flex-shrink-0" style="background-color: ${statusColor}; box-shadow: 0 0 8px ${statusColor}66;" title="${s.status}"></div>
                </div>
                <div class="space-y-xs mb-lg flex-1">
                    <div class="flex justify-between text-body-sm font-body-sm border-b border-surface-variant pb-xs">
                        <span class="text-secondary">Connector</span>
                        <span class="font-semibold px-2 py-0.5 bg-blue-50 text-blue-700 text-[10px] rounded">${s.connector_type}</span>
                    </div>
                    <div class="flex justify-between text-body-sm font-body-sm border-b border-surface-variant pb-xs pt-xs">
                        <span class="text-secondary">Sync Frequency</span>
                        <span class="font-semibold">${syncFreq}</span>
                    </div>
                    <div class="flex justify-between text-body-sm font-body-sm pt-xs">
                        <span class="text-secondary">Website</span>
                        <a href="${s.website_url}" target="_blank" class="font-semibold text-primary hover:underline truncate max-w-[150px] text-right">Link</a>
                    </div>
                </div>
                <div class="flex items-center gap-sm mt-auto pt-md border-t border-surface-variant">
                    <button onclick="triggerCrawl(${s.id})" class="flex-1 font-label-md text-label-md py-xs rounded bg-surface border border-outline-variant text-on-surface hover:bg-surface-variant transition-colors flex justify-center items-center gap-xs">
                        <span class="material-symbols-outlined text-[18px]">sync</span> Crawl
                    </button>
                    <button onclick="viewCrawlLogs(${s.id})" class="px-sm py-xs rounded text-secondary hover:bg-surface-variant transition-colors" title="View Logs">
                        <span class="material-symbols-outlined text-[20px]">list_alt</span>
                    </button>
                    <button class="px-sm py-xs rounded text-secondary hover:bg-surface-variant transition-colors" title="Settings">
                        <span class="material-symbols-outlined text-[20px]">more_vert</span>
                    </button>
                </div>
            </div>
        `;
    }).join("");
}

function bindNewSourceButton() {
    const btns = document.querySelectorAll("button");
    btns.forEach(btn => {
        if (btn.textContent.toLowerCase().includes("source") || btn.textContent.toLowerCase().includes("portal")) {
            btn.onclick = (e) => {
                e.preventDefault();
                openSourceModal();
            };
        }
    });
}

function injectSourceModal() {
    if (document.getElementById("source-modal")) return;

    const modalHtml = `
        <div id="source-modal" class="hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-md">
            <div class="bg-surface-container-lowest max-w-xl w-full rounded-xl p-xl shadow-2xl space-y-lg relative text-on-surface">
                <button onclick="closeSourceModal()" class="absolute top-md right-md text-outline hover:text-on-surface">
                    <span class="material-symbols-outlined text-2xl">close</span>
                </button>

                <h2 class="font-bold text-xl text-on-surface flex items-center gap-sm">
                    <span class="material-symbols-outlined text-primary">language</span>
                    Configure Procurement Source Portal
                </h2>

                <form id="source-form" class="space-y-md" onsubmit="saveSource(event)">
                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">Portal Name *</label>
                        <input type="text" id="src-name" required class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="e.g. Government e-Marketplace (GeM)" />
                    </div>

                    <div class="grid grid-cols-2 gap-md">
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Website URL *</label>
                            <input type="url" id="src-url" required class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="https://gem.gov.in" />
                        </div>
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Search URL (Optional)</label>
                            <input type="url" id="src-search-url" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="https://gem.gov.in/search?q=lms" />
                        </div>
                    </div>

                    <div class="grid grid-cols-3 gap-md">
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Connector Type</label>
                            <select id="src-connector-type" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface">
                                <option value="Public">Public Website</option>
                                <option value="Playwright">Playwright Browser</option>
                                <option value="RSS">RSS Feed</option>
                                <option value="API">REST API</option>
                                <option value="Auth">Authenticated Login</option>
                            </select>
                        </div>
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Country</label>
                            <input type="text" id="src-country" value="India" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" />
                        </div>
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Category</label>
                            <select id="src-category" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface">
                                <option value="Government">Government</option>
                                <option value="Corporate">Corporate</option>
                                <option value="NGOs">NGOs</option>
                                <option value="International">International</option>
                            </select>
                        </div>
                    </div>

                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">Tender CSS Selector (Optional)</label>
                        <input type="text" id="src-selector" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder=".bid-card, table tr, article" />
                    </div>

                    <div class="grid grid-cols-2 gap-md">
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Frequency</label>
                            <select id="src-frequency" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface">
                                <option value="daily">Daily</option>
                                <option value="hourly">Hourly</option>
                                <option value="manual">Manual</option>
                            </select>
                        </div>
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Priority (1-5)</label>
                            <input type="number" min="1" max="5" id="src-priority" value="5" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" />
                        </div>
                    </div>

                    <div class="flex justify-end gap-md pt-md border-t border-outline-variant">
                        <button type="button" onclick="closeSourceModal()" class="px-md py-sm bg-surface-container-high font-semibold text-sm rounded-lg">Cancel</button>
                        <button type="submit" class="px-md py-sm bg-primary text-on-primary font-semibold text-sm rounded-lg hover:bg-surface-tint">Save Source</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML("beforeend", modalHtml);
}

function openSourceModal() {
    const modal = document.getElementById("source-modal");
    if (modal) modal.classList.remove("hidden");
}

function closeSourceModal() {
    const modal = document.getElementById("source-modal");
    if (modal) modal.classList.add("hidden");
}

async function saveSource(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById("src-name").value.trim(),
        website_url: document.getElementById("src-url").value.trim(),
        search_url: document.getElementById("src-search-url").value.trim() || undefined,
        connector_type: document.getElementById("src-connector-type").value,
        country: document.getElementById("src-country").value.trim() || "India",
        category: document.getElementById("src-category").value,
        tender_selector: document.getElementById("src-selector").value.trim() || undefined,
        frequency: document.getElementById("src-frequency").value,
        priority: parseInt(document.getElementById("src-priority").value) || 1
    };

    try {
        const res = await fetch("/api/v1/sources", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            closeSourceModal();
            loadSources();
        } else {
            alert("Failed to add source portal.");
        }
    } catch (e) {
        console.error("Save source error:", e);
    }
}

async function triggerCrawl(id) {
    alert("⚡ Initiating live portal web crawl...");
    const res = await fetch(`/api/v1/sources/${id}/run-crawl`, { method: "POST" });
    if (res.ok) {
        const data = await res.json();
        alert(`✅ Crawl completed! Found ${data.found_tenders} tenders, extracted ${data.new_tenders} new opportunities.`);
        loadSources();
    }
}

async function viewCrawlLogs(id) {
    try {
        const res = await fetch(`/api/v1/sources/${id}/logs`);
        if (res.ok) {
            const logs = await res.json();
            showLogsModal(logs);
        }
    } catch (e) {
        console.error("Logs error:", e);
    }
}

function showLogsModal(logs) {
    let modal = document.getElementById("logs-modal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "logs-modal";
        modal.className = "fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex items-center justify-center p-md";
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div class="bg-surface-container-lowest max-w-2xl w-full max-h-[80vh] overflow-y-auto rounded-xl p-xl shadow-2xl space-y-md relative">
            <button onclick="document.getElementById('logs-modal').remove()" class="absolute top-md right-md text-outline hover:text-on-surface">
                <span class="material-symbols-outlined text-2xl">close</span>
            </button>
            <h3 class="font-bold text-lg text-on-surface">Portal Crawl Execution Logs</h3>
            <div class="space-y-xs text-xs font-mono">
                ${logs.length === 0 ? '<p class="text-secondary">No crawl runs recorded yet.</p>' : logs.map(l => `
                    <div class="p-sm bg-surface-container rounded border border-outline-variant/30 flex justify-between items-center">
                        <div>
                            <span class="font-bold text-primary">${new Date(l.start_time).toLocaleString()}</span>
                            <span class="text-secondary block">Found: ${l.opportunities_found} • New: ${l.new_opportunities} • Duration: ${l.duration_seconds}s</span>
                        </div>
                        <span class="px-2 py-0.5 rounded font-bold ${l.status === 'completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}">${l.status}</span>
                    </div>
                `).join("")}
            </div>
        </div>
    `;
}

async function togglePause(id) {
    await fetch(`/api/v1/sources/${id}/toggle-pause`, { method: "POST" });
    loadSources();
}

async function deleteSource(id) {
    if (confirm("Are you sure you want to delete this procurement source?")) {
        await fetch(`/api/v1/sources/${id}`, { method: "DELETE" });
        loadSources();
    }
}
