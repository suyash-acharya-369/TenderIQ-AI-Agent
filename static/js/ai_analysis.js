// TenderIQ AI Deep Analysis Controller
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("ai-analysis")) {
        initAIAnalysisPage();
    }
});

let allTenders = [];
let selectedTender = null;

async function initAIAnalysisPage() {
    try {
        const res = await fetch("/api/v1/tenders");
        if (res.ok) {
            allTenders = await res.json();
            if (allTenders.length > 0) {
                renderTenderDropdown(allTenders);
                renderAIAnalysis(allTenders[0]);
            }
        }
    } catch (e) {
        console.error("Error loading tenders for AI analysis:", e);
    }
}

function renderTenderDropdown(tenders) {
    const headerContainer = document.querySelector("header .flex.items-center.gap-md") || document.querySelector("header");
    if (!headerContainer || document.getElementById("ai-tender-select")) return;

    const selectHtml = `
        <div class="flex items-center gap-xs ml-auto">
            <label class="text-xs font-bold text-secondary">Select Tender:</label>
            <select id="ai-tender-select" class="p-xs text-xs border border-outline-variant rounded-lg bg-surface text-on-surface max-w-xs font-medium">
                ${tenders.map(t => `<option value="${t.id}">${t.tender_number} - ${t.title.substring(0, 45)}...</option>`).join("")}
            </select>
            <button onclick="runSelectedAI()" class="px-sm py-xs bg-primary text-on-primary rounded text-xs font-semibold hover:bg-surface-tint flex items-center gap-xs shadow-sm">
                <span class="material-symbols-outlined text-[14px]">auto_awesome</span>
                Re-Run AI
            </button>
        </div>
    `;

    headerContainer.insertAdjacentHTML("beforeend", selectHtml);

    document.getElementById("ai-tender-select").addEventListener("change", (e) => {
        const targetId = parseInt(e.target.value);
        const found = allTenders.find(t => t.id === targetId);
        if (found) {
            renderAIAnalysis(found);
        }
    });
}

function renderAIAnalysis(t) {
    selectedTender = t;

    // Update Title & Number
    const titleEl = document.querySelector("h2");
    if (titleEl) {
        titleEl.innerHTML = `
            ${t.title}
            <span class="bg-purple-100 text-purple-700 px-sm py-xs rounded-lg text-xs border border-purple-200 inline-flex items-center gap-xs ml-sm font-bold">
                <span class="material-symbols-outlined text-[14px]">auto_awesome</span>
                AI Score ${t.overall_match_score}%
            </span>
        `;
    }

    // Find and update sections if present
    const tenderNumEls = document.querySelectorAll("[data-tender-num]");
    tenderNumEls.forEach(el => el.textContent = t.tender_number);

    const scopeContainer = document.getElementById("ai-scope-content");
    if (scopeContainer) {
        scopeContainer.textContent = t.scope_of_work || "No scope details extracted yet.";
    }

    const summaryContainer = document.getElementById("ai-summary-content");
    if (summaryContainer) {
        summaryContainer.textContent = t.ai_summary || "High match strategic opportunity for digital learning platform execution.";
    }

    const riskContainer = document.getElementById("ai-risk-content");
    if (riskContainer) {
        riskContainer.textContent = t.risk_analysis || "Low to moderate timeline adherence risk.";
    }
}

async function runSelectedAI() {
    if (!selectedTender) return;
    
    alert(`⚡ Contacting OpenRouter AI engine for tender ${selectedTender.tender_number}...`);
    try {
        const res = await fetch(`/api/v1/tenders/${selectedTender.id}/run-ai`, { method: "POST" });
        if (res.ok) {
            const updated = await res.json();
            alert("✅ OpenRouter AI Analysis re-generated successfully!");
            renderAIAnalysis(updated);
        } else {
            alert("Failed to re-run AI analysis.");
        }
    } catch (e) {
        console.error("AI run error:", e);
        alert("Error connecting to AI service.");
    }
}
