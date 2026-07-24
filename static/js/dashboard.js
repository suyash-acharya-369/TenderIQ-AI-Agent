// TenderIQ AI Command Center Engine - Production Grade Real-Time Analytics
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname === "/" || window.location.pathname.includes("dashboard")) {
        loadDashboardData();
        setupGlobalSearch();
        setInterval(loadDashboardData, 10000); // 10s live pulse
    }
});

async function loadDashboardData() {
    try {
        // Fetch KPIs
        const kpiRes = await fetch("/api/v1/dashboard/kpis");
        if (kpiRes.ok) {
            const data = await kpiRes.json();
            updateKPIs(data);
        }

        // Fetch Distribution
        const distRes = await fetch("/api/v1/dashboard/distribution");
        if (distRes.ok) {
            const dist = await distRes.json();
            renderGlobalDistribution(dist);
        }

        // Fetch Trends
        const trendRes = await fetch("/api/v1/dashboard/trends");
        if (trendRes.ok) {
            const trendData = await trendRes.json();
            renderOpportunityTrends(trendData);
        }

        // Fetch Live Feed
        const feedRes = await fetch("/api/v1/dashboard/live-feed");
        if (feedRes.ok) {
            const feed = await feedRes.json();
            renderLiveFeed(feed);
        }
    } catch (e) {
        console.error("[Dashboard] Error loading data:", e);
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
            const val = data.pipeline_value_inr || 0;
            if (val >= 10000000) {
                el.textContent = `₹ ${(val / 10000000).toFixed(2)} Cr`;
            } else if (val >= 100000) {
                el.textContent = `₹ ${(val / 100000).toFixed(1)} L`;
            } else {
                el.textContent = `₹ ${val.toLocaleString()}`;
            }
        }
    });
}

function renderGlobalDistribution(dist) {
    const container = document.getElementById("distribution-stats");
    if (!container) return;

    if (!dist || dist.length === 0) {
        container.innerHTML = `<div class="p-sm text-xs text-secondary">No regional data available yet.</div>`;
        return;
    }

    container.innerHTML = dist.map(d => `
        <div class="p-sm bg-surface-container-lowest/80 backdrop-blur border border-outline-variant/60 rounded-xl space-y-0.5 shadow-sm">
            <span class="text-xs font-bold text-primary block truncate">${d.region}</span>
            <div class="flex items-baseline justify-between">
                <span class="text-lg font-bold text-on-surface">${d.count} <span class="text-[10px] text-secondary font-normal">tenders</span></span>
                <span class="text-xs font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded">${d.percentage}%</span>
            </div>
            <span class="text-[11px] text-secondary block font-medium">₹ ${(d.total_value_inr / 100000).toFixed(1)} L</span>
        </div>
    `).join("");
}

function renderOpportunityTrends(data) {
    const container = document.getElementById("opportunity-trend-container");
    if (!container) return;

    const buckets = data.buckets || [];
    const maxCount = Math.max(...buckets.map(b => b.count), 1);

    container.innerHTML = `
        <div class="w-full h-full flex items-end justify-around px-md pb-xs z-10">
            ${buckets.map(b => {
                const heightPercent = Math.max(round((b.count / maxCount) * 80), 20);
                return `
                    <div class="flex flex-col items-center gap-1 group relative cursor-pointer" onclick="window.location.href='/opportunities'">
                        <span class="text-xs font-bold text-on-surface">${b.count}</span>
                        <div class="w-12 rounded-t-lg transition-all group-hover:brightness-110 shadow-sm" style="height: ${heightPercent}%; background-color: ${b.color}"></div>
                        <span class="text-[11px] font-medium text-secondary truncate max-w-[90px] text-center mt-1">${b.label.split(' ')[0]}</span>
                    </div>
                `;
            }).join("")}
        </div>
        <svg class="absolute inset-0 w-full h-full pointer-events-none opacity-40" preserveaspectratio="none" viewbox="0 0 100 100">
            <path d="M0,80 Q33,40 66,50 T100,20" fill="none" stroke="#8a2be2" stroke-dasharray="4 2" stroke-width="2" vector-effect="non-scaling-stroke"></path>
        </svg>
    `;
}

function renderLiveFeed(feed) {
    const container = document.getElementById("dashboard-live-feed");
    if (!container) return;

    if (!feed || feed.length === 0) {
        container.innerHTML = `<p class="text-xs text-secondary p-md">No live tender activity detected yet.</p>`;
        return;
    }

    container.innerHTML = feed.map(item => `
        <div onclick="openTenderModal(${item.id})" class="flex gap-md p-sm rounded-lg hover:bg-surface-container-low transition-colors cursor-pointer ${item.match_score >= 85 ? 'ai-border-accent bg-[#8a2be2]/5' : ''}">
            <div class="w-8 h-8 rounded-full ${item.match_score >= 85 ? 'bg-[#8a2be2]/10 text-[#8a2be2]' : 'bg-primary-container text-on-primary-container'} flex items-center justify-center flex-shrink-0">
                <span class="material-symbols-outlined text-[16px]">${item.match_score >= 85 ? 'psychology' : 'description'}</span>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-xs">
                    <span class="font-bold text-xs text-primary line-clamp-1">${item.tender_number}</span>
                    <span class="px-1.5 py-0.5 ${item.match_score >= 85 ? 'bg-purple-100 text-purple-700 font-bold' : 'bg-gray-100 text-gray-700'} text-[10px] rounded-full shrink-0">${item.match_score}% Match</span>
                </div>
                <p class="font-body-sm text-xs text-on-surface font-semibold line-clamp-1 mt-0.5">${item.title}</p>
                <p class="text-[11px] text-secondary line-clamp-2 mt-0.5">${item.ai_summary}</p>
                <div class="flex items-center gap-xs mt-xs text-[10px] text-secondary">
                    <span>${item.org_name}</span>
                    <span>•</span>
                    <span>${item.value_str}</span>
                    <span>•</span>
                    <span class="text-primary font-medium hover:underline">Click to view detail</span>
                </div>
            </div>
        </div>
    `).join("");
}

function setupGlobalSearch() {
    const input = document.getElementById("global-search-input");
    if (input) {
        input.addEventListener("keyup", (e) => {
            if (e.key === "Enter") {
                const query = e.target.value.trim();
                if (query) {
                    window.location.href = `/opportunities?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }
}

async function triggerRealtimeCrawl() {
    showToast("⚡ Initiating live web crawl & OpenRouter AI analysis...", "info");

    try {
        const sourcesRes = await fetch("/api/v1/sources");
        if (sourcesRes.ok) {
            const sources = await sourcesRes.json();
            const activeSources = sources.filter(s => s.status === 'active');
            if (activeSources.length > 0) {
                const target = activeSources[0];
                const res = await fetch(`/api/v1/sources/${target.id}/run-crawl`, { method: "POST" });
                if (res.ok) {
                    const data = await res.json();
                    showToast(`✅ Live search complete! Discovered ${data.new_tenders} new opportunities.`, "success");
                } else {
                    showToast("Failed to complete portal crawl.", "error");
                }
            } else {
                showToast("No active portal sources configured.", "warning");
            }
        }
        await loadDashboardData();
    } catch (e) {
        console.error("Crawl error:", e);
        showToast("Error initiating real-time search.", "error");
    }
}

async function generateAIBrief() {
    showToast("🤖 Contacting OpenRouter AI for executive intelligence briefing...", "info");
    try {
        const res = await fetch("/api/v1/dashboard/ai-brief", { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            openAIBriefModal(data);
        } else {
            showToast("Failed to generate AI briefing.", "error");
        }
    } catch (e) {
        console.error("AI Brief error:", e);
        showToast("Error connecting to AI service.", "error");
    }
}

function openAIBriefModal(data) {
    let modal = document.getElementById("ai-brief-modal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "ai-brief-modal";
        modal.className = "fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex items-center justify-center p-md";
        document.body.appendChild(modal);
    }

    const recsHtml = (data.top_recommendations || []).map(r => `
        <div class="p-md bg-surface-container rounded-lg space-y-1 cursor-pointer hover:bg-surface-container-high transition-colors" onclick="document.getElementById('ai-brief-modal').remove(); openTenderModal(${r.id});">
            <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-primary">${r.tender_number}</span>
                <span class="px-2 py-0.5 bg-purple-100 text-purple-700 font-bold text-xs rounded-full">${r.score}% Match</span>
            </div>
            <h4 class="font-bold text-sm text-on-surface line-clamp-1">${r.title}</h4>
            <div class="flex items-center justify-between text-xs text-secondary">
                <span>Recommendation: <strong class="text-emerald-600">${r.recommendation}</strong></span>
                <span>Win Prob: <strong>${r.win_probability}%</strong></span>
            </div>
        </div>
    `).join("");

    modal.innerHTML = `
        <div class="bg-surface-container-lowest max-w-2xl w-full max-h-[90vh] overflow-y-auto rounded-xl p-xl shadow-2xl space-y-lg relative text-on-surface">
            <button onclick="document.getElementById('ai-brief-modal').remove()" class="absolute top-md right-md text-outline hover:text-on-surface">
                <span class="material-symbols-outlined text-2xl">close</span>
            </button>

            <div class="flex items-center gap-md border-b border-outline-variant pb-md">
                <div class="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shadow-sm">
                    <span class="material-symbols-outlined text-2xl">psychology</span>
                </div>
                <div>
                    <h2 class="font-bold text-xl text-on-surface">${data.brief_title}</h2>
                    <p class="text-xs text-secondary">Generated via OpenRouter AI • ${new Date(data.generated_at).toLocaleTimeString()}</p>
                </div>
            </div>

            <div class="space-y-sm">
                <h3 class="font-bold text-sm text-on-surface flex items-center gap-xs">
                    <span class="material-symbols-outlined text-[#8a2be2]">auto_awesome</span>
                    Executive Summary
                </h3>
                <p class="text-sm text-secondary bg-surface-container p-md rounded-lg leading-relaxed">${data.ai_summary}</p>
            </div>

            <div class="space-y-sm">
                <h3 class="font-bold text-sm text-on-surface flex items-center gap-xs">
                    <span class="material-symbols-outlined text-amber-600">warning</span>
                    Risk & Strategy Evaluation
                </h3>
                <p class="text-sm text-secondary bg-amber-50 border border-amber-200 p-md rounded-lg leading-relaxed">${data.risk_analysis}</p>
            </div>

            <div class="space-y-sm">
                <h3 class="font-bold text-sm text-on-surface">Top Recommended Bids</h3>
                <div class="space-y-sm">${recsHtml}</div>
            </div>

            <div class="flex justify-end gap-md pt-md border-t border-outline-variant">
                <button onclick="navigator.clipboard.writeText('${data.ai_summary}'); showToast('AI Brief copied to clipboard!', 'success');" class="px-md py-sm bg-surface-container-high text-on-surface font-semibold text-sm rounded-lg hover:bg-surface-container">
                    Copy Text
                </button>
                <button onclick="document.getElementById('ai-brief-modal').remove()" class="px-md py-sm bg-primary text-on-primary font-semibold text-sm rounded-lg hover:bg-primary/90">
                    Done
                </button>
            </div>
        </div>
    `;
}

function showToast(message, type = "info") {
    let toast = document.getElementById("dashboard-toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "dashboard-toast";
        toast.className = "fixed bottom-6 right-6 z-50 transition-all duration-300 transform translate-y-full opacity-0";
        document.body.appendChild(toast);
    }

    const bg = type === "success" ? "bg-emerald-800 text-white" : type === "error" ? "bg-red-800 text-white" : "bg-slate-900 text-white";

    toast.className = `fixed bottom-6 right-6 z-50 ${bg} px-md py-sm rounded-xl shadow-2xl flex items-center gap-sm text-xs font-semibold transition-all duration-300 transform translate-y-0 opacity-100`;
    toast.innerHTML = message;

    setTimeout(() => {
        toast.className = "fixed bottom-6 right-6 z-50 transition-all duration-300 transform translate-y-full opacity-0";
    }, 4000);
}

function round(val) {
    return Math.round(val);
}
