// TenderIQ AI Dashboard Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname === "/" || window.location.pathname.includes("dashboard")) {
        loadDashboardData();
    }
});

async function loadDashboardData() {
    try {
        const res = await fetch("/api/v1/dashboard/kpis");
        if (res.ok) {
            const data = await res.json();
            updateKPIs(data);
        }

        const crawlsRes = await fetch("/api/v1/dashboard/recent-crawls");
        if (crawlsRes.ok) {
            const crawls = await crawlsRes.json();
            renderRecentCrawls(crawls);
        }

        const aiRes = await fetch("/api/v1/dashboard/recent-ai");
        if (aiRes.ok) {
            const aiData = await aiRes.json();
            renderRecentAI(aiData);
        }
    } catch (e) {
        console.error("Error loading dashboard data:", e);
    }
}

function updateKPIs(data) {
    const kpiElements = document.querySelectorAll("[data-kpi]");
    kpiElements.forEach(el => {
        const key = el.getAttribute("data-kpi");
        if (key === "total") el.textContent = data.total_opportunities;
        if (key === "high_priority") el.textContent = data.high_priority;
        if (key === "closing_soon") el.textContent = data.closing_soon;
        if (key === "pipeline") {
            const valInLakhs = (data.pipeline_value_inr / 100000).toFixed(1);
            el.textContent = `₹ ${valInLakhs} Lakhs`;
        }
    });
}

function renderRecentCrawls(crawls) {
    const container = document.getElementById("recent-crawls-tbody");
    if (!container) return;
    container.innerHTML = crawls.map(c => `
        <tr class="border-b border-outline-variant/30 hover:bg-surface-container-low transition-colors">
            <td class="py-sm px-md font-medium text-on-surface">${c.source_name}</td>
            <td class="py-sm px-md text-secondary">${new Date(c.start_time).toLocaleTimeString()}</td>
            <td class="py-sm px-md text-secondary">${c.opportunities_found} found</td>
            <td class="py-sm px-md">
                <span class="px-sm py-xs rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">${c.status}</span>
            </td>
        </tr>
    `).join("");
}

function renderRecentAI(aiData) {
    const container = document.getElementById("recent-ai-container");
    if (!container) return;
    container.innerHTML = aiData.map(item => `
        <div class="p-md bg-surface-container-lowest border border-outline-variant rounded-xl space-y-xs hover:border-primary transition-all">
            <div class="flex items-center justify-between">
                <span class="font-bold text-xs text-primary">${item.tender_number}</span>
                <span class="px-sm py-xs bg-purple-100 text-purple-700 font-bold text-xs rounded-full">${item.overall_match_score}% Match</span>
            </div>
            <h4 class="font-bold text-sm text-on-surface line-clamp-1">${item.title}</h4>
            <p class="text-xs text-secondary line-clamp-2">${item.ai_summary || "AI Analysis completed."}</p>
        </div>
    `).join("");
}
