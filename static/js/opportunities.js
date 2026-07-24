// TenderIQ AI Operational Intelligence Explorer Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("opportunities")) {
        initTenderIntelligencePage();
    } else if (window.location.pathname.includes("opportunity-details")) {
        initOpportunityDetailsPage();
    }
});

let currentTenders = [];
let allKeywordGroups = [];
let allSources = [];
let allOrganizations = [];

async function initTenderIntelligencePage() {
    await loadFilterDropdowns();
    setupFilterListeners();
    loadTenders();
}

async function loadFilterDropdowns() {
    try {
        const [kwRes, srcRes, orgRes] = await Promise.all([
            fetch("/api/v1/keywords"),
            fetch("/api/v1/sources"),
            fetch("/api/v1/organizations")
        ]);

        if (kwRes.ok) {
            allKeywordGroups = await kwRes.json();
            populateKeywordDropdown(allKeywordGroups);
        }
        if (srcRes.ok) {
            allSources = await srcRes.json();
            populateSourceDropdown(allSources);
        }
        if (orgRes.ok) {
            allOrganizations = await orgRes.json();
            populateOrgDropdown(allOrganizations);
        }
    } catch (e) {
        console.error("Error populating Tender Intelligence filter dropdowns:", e);
    }
}

function populateKeywordDropdown(groups) {
    const select = document.getElementById("filter-keyword-group");
    if (!select) return;
    select.innerHTML = '<option value="">All Keyword Groups (10 Domain Categories)</option>' +
        groups.map(g => `<option value="${g.id}">🎯 ${g.name} (${(g.positive_keywords || []).slice(0, 3).join(", ")})</option>`).join("");
}

function populateSourceDropdown(sources) {
    const select = document.getElementById("filter-source-portal");
    if (!select) return;
    select.innerHTML = '<option value="">All Procurement Portals (GeM, CPPP, UNGM...)</option>' +
        sources.map(s => `<option value="${s.id}">🌐 ${s.name} (${s.connector_type})</option>`).join("");
}

function populateOrgDropdown(orgs) {
    const select = document.getElementById("filter-organization");
    if (!select) return;
    select.innerHTML = '<option value="">All Organizations</option>' +
        orgs.map(o => `<option value="${o.id}">${o.name}</option>`).join("");
}

function setupFilterListeners() {
    const filterIds = [
        "filter-keyword-group", "filter-source-portal", "filter-match-score",
        "filter-recommendation", "filter-status", "filter-date-range",
        "filter-organization", "filter-country", "search-input"
    ];

    filterIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("change", () => loadTenders());
            if (id === "search-input" || id === "filter-country") {
                el.addEventListener("input", debounce(() => loadTenders(), 300));
            }
        }
    });
}

function resetTenderFilters() {
    [
        "filter-keyword-group", "filter-source-portal", "filter-match-score",
        "filter-recommendation", "filter-status", "filter-date-range",
        "filter-organization", "filter-country", "search-input"
    ].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = "";
    });
    loadTenders();
}

function buildFilterQueryParams() {
    const params = new URLSearchParams();
    const q = document.getElementById("search-input")?.value.trim();
    const kwId = document.getElementById("filter-keyword-group")?.value;
    const srcId = document.getElementById("filter-source-portal")?.value;
    const minScore = document.getElementById("filter-match-score")?.value;
    const rec = document.getElementById("filter-recommendation")?.value;
    const status = document.getElementById("filter-status")?.value;
    const dateRange = document.getElementById("filter-date-range")?.value;
    const orgId = document.getElementById("filter-organization")?.value;
    const country = document.getElementById("filter-country")?.value.trim();

    if (q) params.set("q", q);
    if (kwId) params.set("keyword_group_id", kwId);
    if (srcId) params.set("source_id", srcId);
    if (minScore) params.set("min_score", minScore);
    if (rec) params.set("recommendation", rec);
    if (status) params.set("status", status);
    if (dateRange) params.set("date_range", dateRange);
    if (orgId) params.set("organization_id", orgId);
    if (country) params.set("country", country);

    return params.toString();
}

async function loadTenders() {
    const container = document.getElementById("tenders-container") || document.querySelector("main .flex-1");
    if (!container) return;

    const queryString = buildFilterQueryParams();
    const url = queryString ? `/api/v1/tenders?${queryString}` : "/api/v1/tenders";

    try {
        const res = await fetch(url);
        if (res.ok) {
            currentTenders = await res.json();
            renderTenderCards(currentTenders);
        }
    } catch (e) {
        console.error("Error loading tenders:", e);
    }
}

function renderTenderCards(tenders) {
    const container = document.getElementById("tenders-container") || document.querySelector(".max-w-container-max");
    if (!container) return;

    if (tenders.length === 0) {
        container.innerHTML = `
            <div class="p-xl bg-surface-container-lowest border border-outline-variant rounded-xl text-center space-y-md my-md">
                <span class="material-symbols-outlined text-4xl text-outline">search_off</span>
                <h3 class="font-bold text-lg text-on-surface">No Procurement Opportunities Matched Your Filters</h3>
                <p class="text-xs text-secondary max-w-md mx-auto">Try selecting a different Keyword Group, Portal Source, or clearing search parameters.</p>
                <button onclick="resetTenderFilters()" class="px-md py-sm bg-primary text-on-primary text-xs font-semibold rounded-lg hover:bg-surface-tint">Reset All Filters</button>
            </div>
        `;
        return;
    }

    const cardsHtml = tenders.map(t => {
        // Derive matched keyword tags
        const matchedKwBadges = (allKeywordGroups || []).filter(g => 
            (g.positive_keywords || []).some(k => (t.title + " " + (t.scope_of_work || "")).toLowerCase().includes(k.toLowerCase()))
        ).slice(0, 4);

        const sourceName = t.source ? t.source.name : 'Crawled Source';
        const orgName = t.organization ? t.organization.name : 'Procurement Board';

        return `
            <div class="p-lg bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm hover:shadow-md transition-all space-y-md mb-md relative">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-md border-b border-outline-variant/30 pb-sm">
                    <div>
                        <div class="flex items-center gap-xs flex-wrap mb-xs">
                            <span class="px-2 py-0.5 bg-blue-100 text-blue-800 text-[11px] font-bold rounded-full">${sourceName}</span>
                            <span class="px-2 py-0.5 bg-slate-100 text-slate-700 text-[11px] font-semibold rounded-full">${orgName} • ${t.country}</span>
                            <span class="text-xs font-bold text-primary font-mono ml-auto md:ml-0">${t.tender_number}</span>
                        </div>
                        <h3 class="font-bold text-lg text-on-surface hover:text-primary transition-colors cursor-pointer" onclick="openTenderModal(${t.id})">
                            ${t.title}
                        </h3>
                    </div>
                    <div class="flex items-center gap-sm shrink-0">
                        <div class="text-right">
                            <span class="px-md py-xs bg-purple-100 text-purple-700 font-extrabold text-sm rounded-lg border border-purple-200 block">
                                ${t.overall_match_score}% Match
                            </span>
                            <span class="text-[10px] text-emerald-600 font-bold uppercase block mt-1">
                                ${t.bid_recommendation || 'Bid'} (${t.winning_probability || 90}% Win Prob)
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Scope & AI Summary Snippet -->
                <p class="text-xs text-secondary line-clamp-2 leading-relaxed bg-surface p-sm rounded-lg border border-outline-variant/20">
                    <strong class="text-on-surface">AI Summary:</strong> ${t.ai_summary || t.scope_of_work || 'Indexed procurement RFP opportunity.'}
                </p>

                <!-- Keyword Match Pills -->
                <div class="flex items-center gap-xs flex-wrap">
                    <span class="text-[10px] font-bold text-secondary uppercase tracking-wider">Matched Categories:</span>
                    ${matchedKwBadges.length > 0 ? matchedKwBadges.map(b => `<span class="px-2 py-0.5 text-[10px] font-bold rounded-md" style="background-color: ${b.color}15; color: ${b.color}; border: 1px solid ${b.color}30;">${b.name}</span>`).join("") : `<span class="px-2 py-0.5 bg-purple-50 text-purple-700 text-[10px] font-bold rounded-md border border-purple-200">Education & Digital Learning</span>`}
                </div>

                <!-- Footer Meta & Direct Download Links -->
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-sm pt-sm border-t border-outline-variant/30 text-xs text-secondary">
                    <div>
                        <span><strong>Budget:</strong> ${t.budget ? '₹ ' + (t.budget/100000).toFixed(1) + ' Lakhs' : 'Undisclosed'}</span>
                        <span class="mx-xs">•</span>
                        <span><strong>Deadline:</strong> ${t.submission_deadline ? new Date(t.submission_deadline).toLocaleDateString() : 'Open'}</span>
                    </div>

                    <div class="flex items-center gap-xs flex-wrap">
                        ${t.official_link && t.official_link.toLowerCase().endsWith('.pdf') ? `
                            <a href="${t.official_link}" download target="_blank" class="px-sm py-xs bg-emerald-50 text-emerald-700 text-xs font-semibold rounded hover:bg-emerald-100 border border-emerald-200 flex items-center gap-xs">
                                <span class="material-symbols-outlined text-sm">download</span> Download PDF
                            </a>
                        ` : ''}
                        <a href="${t.official_link || '#'}" target="_blank" class="px-sm py-xs bg-surface-container-high text-on-surface text-xs font-semibold rounded hover:bg-surface-container flex items-center gap-xs">
                            <span class="material-symbols-outlined text-sm">open_in_new</span> Official Portal
                        </a>
                        <a href="/opportunity-details?id=${t.id}" class="px-sm py-xs bg-primary text-on-primary text-xs font-semibold rounded hover:bg-surface-tint flex items-center gap-xs">
                            <span class="material-symbols-outlined text-sm">visibility</span> View Details
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join("");

    container.innerHTML = cardsHtml;
}

async function triggerTenderAI(id) {
    if (typeof showGlobalToast === "function") showGlobalToast("Contacting OpenRouter AI engine for analysis...", "info");
    const res = await fetch(`/api/v1/tenders/${id}/run-ai`, { method: "POST" });
    if (res.ok) {
        if (typeof showGlobalToast === "function") showGlobalToast("AI Analysis Re-Calculated!", "success");
        loadTenders();
    }
}

function openTenderModal(id) {
    window.location.href = `/opportunity-details?id=${id}`;
}

async function initOpportunityDetailsPage() {
    const params = new URLSearchParams(window.location.search);
    const tenderId = params.get("id") || 1;

    try {
        const res = await fetch(`/api/v1/tenders/${tenderId}`);
        if (res.ok) {
            const tender = await res.json();
            populateOpportunityDetailsDOM(tender);
        } else {
            const allRes = await fetch("/api/v1/tenders");
            if (allRes.ok) {
                const list = await allRes.json();
                if (list.length > 0) populateOpportunityDetailsDOM(list[0]);
            }
        }
    } catch (e) {
        console.error("Error loading opportunity details:", e);
    }
}

function populateOpportunityDetailsDOM(t) {
    const titleH1 = document.querySelector("h1.text-display-lg") || document.querySelector("main h1") || document.querySelector("h1");
    if (titleH1) titleH1.textContent = t.title;

    const tenderNumSpan = document.querySelector(".font-label-sm.text-secondary") || document.querySelector("main p");
    if (tenderNumSpan) tenderNumSpan.textContent = `Tender No: ${t.tender_number} • Sector: ${t.sector} • Country: ${t.country}`;

    const scoreEls = document.querySelectorAll("[data-score]");
    scoreEls.forEach(el => el.textContent = `${t.overall_match_score}%`);

    const budgetEls = document.querySelectorAll("[data-budget]");
    budgetEls.forEach(el => el.textContent = t.budget ? `₹ ${t.budget.toLocaleString()}` : "Undisclosed");
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}
