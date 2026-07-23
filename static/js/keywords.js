// TenderIQ AI Keyword Manager Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("keyword")) {
        loadKeywords();
    }
});

async function loadKeywords() {
    try {
        const res = await fetch("/api/v1/keywords");
        if (res.ok) {
            const groups = await res.json();
            renderKeywordGroups(groups);
        }
    } catch (e) {
        console.error("Error loading keywords:", e);
    }
}

function renderKeywordGroups(groups) {
    const container = document.getElementById("keywords-container") || document.querySelector("main");
    if (!container) return;

    const cardsHtml = groups.map(g => `
        <div class="p-lg bg-surface-container-lowest border border-outline-variant rounded-xl space-y-md shadow-sm hover:border-primary transition-all">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-sm">
                    <span class="w-4 h-4 rounded-full" style="background-color: ${g.color || '#3B82F6'}"></span>
                    <h3 class="font-bold text-lg text-on-surface">${g.name}</h3>
                </div>
                <span class="px-sm py-xs bg-purple-100 text-purple-700 font-bold text-xs rounded-full">Weight: ${g.priority_weight}x</span>
            </div>

            <div class="space-y-xs">
                <span class="text-xs font-bold text-secondary uppercase tracking-wider block">Positive Keywords</span>
                <div class="flex flex-wrap gap-xs">
                    ${(g.positive_keywords || []).map(k => `<span class="px-sm py-xs bg-blue-50 text-blue-700 text-xs rounded-md font-medium border border-blue-200">${k}</span>`).join("")}
                </div>
            </div>

            ${(g.negative_keywords || []).length ? `
                <div class="space-y-xs">
                    <span class="text-xs font-bold text-secondary uppercase tracking-wider block">Negative Filter Keywords</span>
                    <div class="flex flex-wrap gap-xs">
                        ${g.negative_keywords.map(k => `<span class="px-sm py-xs bg-red-50 text-red-700 text-xs rounded-md font-medium border border-red-200">${k}</span>`).join("")}
                    </div>
                </div>
            ` : ''}

            <div class="flex justify-end pt-sm border-t border-outline-variant/30">
                <button onclick="deleteKeywordGroup(${g.id})" class="text-xs text-red-600 font-semibold hover:underline">Delete Group</button>
            </div>
        </div>
    `).join("");

    const wrapper = document.getElementById("keywords-grid");
    if (wrapper) wrapper.innerHTML = cardsHtml;
}

async function deleteKeywordGroup(id) {
    if (confirm("Are you sure you want to delete this keyword group?")) {
        await fetch(`/api/v1/keywords/${id}`, { method: "DELETE" });
        loadKeywords();
    }
}
