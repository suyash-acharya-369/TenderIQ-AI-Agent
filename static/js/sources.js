// TenderIQ AI Source Manager Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("source")) {
        loadSources();
    }
});

async function loadSources() {
    try {
        const res = await fetch("/api/v1/sources");
        if (res.ok) {
            const sources = await res.json();
            renderSourceList(sources);
        }
    } catch (e) {
        console.error("Error loading sources:", e);
    }
}

function renderSourceList(sources) {
    const container = document.getElementById("sources-tbody") || document.querySelector("tbody");
    if (!container) return;

    container.innerHTML = sources.map(s => `
        <tr class="border-b border-outline-variant/30 hover:bg-surface-container-low transition-colors">
            <td class="py-md px-md font-bold text-sm text-on-surface">${s.name}</td>
            <td class="py-md px-md text-xs text-secondary truncate max-w-xs">${s.website_url}</td>
            <td class="py-md px-md text-xs text-on-surface">${s.country} • ${s.category}</td>
            <td class="py-md px-md">
                <span class="px-sm py-xs bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">${s.connector_type}</span>
            </td>
            <td class="py-md px-md">
                <span class="px-sm py-xs ${s.status === 'active' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'} text-xs font-semibold rounded-full">${s.status}</span>
            </td>
            <td class="py-md px-md flex items-center gap-xs">
                <button onclick="triggerCrawl(${s.id})" class="px-sm py-xs bg-primary text-on-primary text-xs font-medium rounded hover:bg-surface-tint">
                    Run Crawl
                </button>
                <button onclick="togglePause(${s.id})" class="px-sm py-xs bg-surface-container-high text-on-surface text-xs font-medium rounded hover:bg-surface-container">
                    ${s.status === 'active' ? 'Pause' : 'Resume'}
                </button>
            </td>
        </tr>
    `).join("");
}

async function triggerCrawl(id) {
    alert("Triggering manual portal crawl & opportunity extraction...");
    const res = await fetch(`/api/v1/sources/${id}/run-crawl`, { method: "POST" });
    if (res.ok) {
        const data = await res.json();
        alert(`Crawl completed! Found ${data.new_tenders} new opportunities.`);
        loadSources();
    }
}

async function togglePause(id) {
    await fetch(`/api/v1/sources/${id}/toggle-pause`, { method: "POST" });
    loadSources();
}
