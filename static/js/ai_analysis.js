// TenderIQ AI Deep Analysis Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("ai-analysis")) {
        loadAIAnalysis();
    }
});

async function loadAIAnalysis() {
    try {
        const res = await fetch("/api/v1/tenders");
        if (res.ok) {
            const tenders = await res.json();
            if (tenders.length > 0) {
                renderTenderAI(tenders[0]);
            }
        }
    } catch (e) {
        console.error("Error loading AI analysis:", e);
    }
}

function renderTenderAI(t) {
    const titleEl = document.querySelector("h2");
    if (titleEl && t.title) {
        titleEl.innerHTML = `
            ${t.title}
            <span class="bg-primary-fixed/20 text-on-primary-fixed px-sm py-xs rounded-DEFAULT font-label-sm text-label-sm border border-primary-fixed/30 flex items-center gap-xs inline-flex ml-sm">
                <span class="material-symbols-outlined text-[14px]" data-icon="auto_awesome">auto_awesome</span>
                AI Analyzed
            </span>
        `;
    }

    const refEl = document.querySelector(".flex.items-center.gap-sm.text-secondary span:last-child");
    if (refEl && t.tender_number) {
        refEl.textContent = t.tender_number;
    }
}
