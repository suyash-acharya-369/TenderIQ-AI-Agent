// TenderIQ AI Opportunities Explorer Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("opportunities")) {
        loadTenders();
        setupSearchInput();
    }
});

let currentTenders = [];

async function loadTenders(query = "") {
    try {
        const url = query ? `/api/v1/tenders?q=${encodeURIComponent(query)}` : "/api/v1/tenders";
        const res = await fetch(url);
        if (res.ok) {
            currentTenders = await res.json();
            renderTenderList(currentTenders);
        }
    } catch (e) {
        console.error("Error loading tenders:", e);
    }
}

function setupSearchInput() {
    const input = document.getElementById("search-input");
    if (input) {
        input.addEventListener("input", (e) => {
            const val = e.target.value;
            loadTenders(val);
        });
    }
}

function renderTenderList(tenders) {
    const container = document.getElementById("tenders-container") || document.querySelector("tbody");
    if (!container) return;

    if (tenders.length === 0) {
        container.innerHTML = `<tr><td colspan="6" class="text-center py-xl text-secondary">No matching opportunities found.</td></tr>`;
        return;
    }

    container.innerHTML = tenders.map(t => `
        <tr class="border-b border-outline-variant/30 hover:bg-surface-container-low transition-colors cursor-pointer" onclick="openTenderModal(${t.id})">
            <td class="py-md px-md">
                <span class="font-bold text-xs text-primary">${t.tender_number}</span>
            </td>
            <td class="py-md px-md max-w-md">
                <p class="font-semibold text-sm text-on-surface line-clamp-1">${t.title}</p>
                <p class="text-xs text-secondary">${t.organization ? t.organization.name : 'Procurement Board'} • ${t.country}</p>
            </td>
            <td class="py-md px-md text-xs text-secondary font-medium">
                ${t.budget ? '₹ ' + (t.budget/100000).toFixed(1) + ' L' : 'N/A'}
            </td>
            <td class="py-md px-md">
                <span class="px-sm py-xs bg-purple-100 text-purple-700 font-bold text-xs rounded-full">${t.overall_match_score}%</span>
            </td>
            <td class="py-md px-md text-xs text-secondary">
                ${t.submission_deadline ? new Date(t.submission_deadline).toLocaleDateString() : 'Open'}
            </td>
            <td class="py-md px-md">
                <button onclick="event.stopPropagation(); triggerTenderAI(${t.id})" class="px-sm py-xs bg-primary text-on-primary rounded text-xs font-medium hover:bg-surface-tint">
                    AI Analysis
                </button>
            </td>
        </tr>
    `).join("");
}

async function triggerTenderAI(id) {
    alert("Running OpenAI AI Summarizer & Bid Analysis...");
    const res = await fetch(`/api/v1/tenders/${id}/run-ai`, { method: "POST" });
    if (res.ok) {
        alert("AI Analysis Completed Successfully!");
        loadTenders();
    }
}

function openTenderModal(id) {
    const tender = currentTenders.find(t => t.id === id);
    if (!tender) return;

    let modal = document.getElementById("tender-detail-modal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "tender-detail-modal";
        modal.className = "fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-md";
        document.body.appendChild(modal);
    }

    modal.innerHTML = `
        <div class="bg-surface-container-lowest max-w-4xl w-full max-h-[90vh] overflow-y-auto rounded-xl p-xl shadow-2xl space-y-lg relative">
            <button onclick="document.getElementById('tender-detail-modal').remove()" class="absolute top-md right-md text-outline hover:text-on-surface">
                <span class="material-symbols-outlined text-2xl">close</span>
            </button>
            
            <div class="flex items-center justify-between border-b border-outline-variant pb-md">
                <div>
                    <span class="text-xs font-bold text-primary">${tender.tender_number}</span>
                    <h2 class="font-bold text-xl text-on-surface">${tender.title}</h2>
                    <p class="text-xs text-secondary">${tender.organization ? tender.organization.name : 'Procurement Board'} | ${tender.country}</p>
                </div>
                <span class="px-md py-sm bg-purple-100 text-purple-700 font-bold text-sm rounded-full">${tender.overall_match_score}% Match Score</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-md">
                <div class="p-md bg-surface-container rounded-lg">
                    <span class="text-xs text-secondary block">Estimated Budget</span>
                    <span class="font-bold text-base text-on-surface">${tender.budget ? '₹ ' + tender.budget.toLocaleString() : 'Undisclosed'}</span>
                </div>
                <div class="p-md bg-surface-container rounded-lg">
                    <span class="text-xs text-secondary block">Bid Recommendation</span>
                    <span class="font-bold text-base text-emerald-600">${tender.bid_recommendation || 'Bid'} (${tender.winning_probability || 90}% Win Prob)</span>
                </div>
                <div class="p-md bg-surface-container rounded-lg">
                    <span class="text-xs text-secondary block">Submission Deadline</span>
                    <span class="font-bold text-base text-on-surface">${tender.submission_deadline ? new Date(tender.submission_deadline).toLocaleDateString() : 'N/A'}</span>
                </div>
            </div>

            <div class="space-y-md">
                <h3 class="font-bold text-md text-on-surface">AI Executive Summary & Scope</h3>
                <p class="text-sm text-secondary bg-surface-container-low p-md rounded-lg leading-relaxed">${tender.scope_of_work || 'No scope details available.'}</p>
            </div>

            <div class="space-y-md">
                <h3 class="font-bold text-md text-on-surface">Eligibility & Requirements</h3>
                <div class="text-sm text-secondary space-y-xs">
                    <p><strong>Eligibility:</strong> ${tender.eligibility_criteria || 'Standard RFP requirements.'}</p>
                    <p><strong>Technical:</strong> ${tender.technical_requirements || 'SCORM 1.2/2004, Cloud LMS.'}</p>
                    <p><strong>Required Documents:</strong> ${tender.required_documents || 'Technical & Financial proposal.'}</p>
                </div>
            </div>

            <div class="flex justify-end gap-md pt-md border-t border-outline-variant">
                <a href="${tender.official_link || '#'}" target="_blank" class="px-md py-sm bg-surface-container-high text-on-surface font-semibold text-sm rounded-lg hover:bg-surface-container">
                    Visit Official Portal
                </a>
                <button onclick="triggerTenderAI(${tender.id}); document.getElementById('tender-detail-modal').remove();" class="px-md py-sm bg-primary text-on-primary font-semibold text-sm rounded-lg hover:bg-surface-tint">
                    Re-Run AI Analysis
                </button>
            </div>
        </div>
    `;
}
