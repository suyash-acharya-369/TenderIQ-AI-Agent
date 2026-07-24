// TenderIQ AI Keyword Manager Engine
document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname.includes("keyword")) {
        loadKeywords();
        injectKeywordGroupModal();
        bindNewKeywordButton();
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
    const wrapper = document.getElementById("keywords-grid") || document.querySelector("main");
    if (!wrapper) return;

    if (groups.length === 0) {
        wrapper.innerHTML = `<p class="p-md text-xs text-secondary">No keyword groups created yet.</p>`;
        return;
    }

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

    wrapper.innerHTML = cardsHtml;
}

function bindNewKeywordButton() {
    const btns = document.querySelectorAll("button");
    btns.forEach(btn => {
        if (btn.textContent.toLowerCase().includes("group") || btn.textContent.toLowerCase().includes("keyword")) {
            btn.onclick = (e) => {
                e.preventDefault();
                openKeywordModal();
            };
        }
    });
}

function injectKeywordGroupModal() {
    if (document.getElementById("keyword-group-modal")) return;

    const modalHtml = `
        <div id="keyword-group-modal" class="hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-md">
            <div class="bg-surface-container-lowest max-w-lg w-full rounded-xl p-xl shadow-2xl space-y-lg relative text-on-surface">
                <button onclick="closeKeywordModal()" class="absolute top-md right-md text-outline hover:text-on-surface">
                    <span class="material-symbols-outlined text-2xl">close</span>
                </button>

                <h2 class="font-bold text-xl text-on-surface flex items-center gap-sm">
                    <span class="material-symbols-outlined text-primary">label</span>
                    Create New Keyword Group
                </h2>

                <form id="keyword-group-form" class="space-y-md" onsubmit="saveKeywordGroup(event)">
                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">Group Name *</label>
                        <input type="text" id="kw-name" required class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="e.g. SCORM Content & E-Learning" />
                    </div>

                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">Positive Keywords (comma-separated) *</label>
                        <input type="text" id="kw-positive" required class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="LMS, E-Learning, SCORM, Storyline" />
                    </div>

                    <div class="space-y-xs">
                        <label class="text-xs font-bold text-on-surface block">Negative / Exclude Keywords (comma-separated)</label>
                        <input type="text" id="kw-negative" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" placeholder="Civil Works, Construction, Hardware" />
                    </div>

                    <div class="grid grid-cols-2 gap-md">
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Priority Weight</label>
                            <input type="number" step="0.1" id="kw-weight" value="1.5" class="w-full p-sm border border-outline-variant rounded-lg text-sm bg-surface" />
                        </div>
                        <div class="space-y-xs">
                            <label class="text-xs font-bold text-on-surface block">Badge Color</label>
                            <input type="color" id="kw-color" value="#8B5CF6" class="w-full h-10 p-xs border border-outline-variant rounded-lg bg-surface" />
                        </div>
                    </div>

                    <div class="flex justify-end gap-md pt-md border-t border-outline-variant">
                        <button type="button" onclick="closeKeywordModal()" class="px-md py-sm bg-surface-container-high font-semibold text-sm rounded-lg">Cancel</button>
                        <button type="submit" class="px-md py-sm bg-primary text-on-primary font-semibold text-sm rounded-lg hover:bg-surface-tint">Create Group</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML("beforeend", modalHtml);
}

function openKeywordModal() {
    const modal = document.getElementById("keyword-group-modal");
    if (modal) modal.classList.remove("hidden");
}

function closeKeywordModal() {
    const modal = document.getElementById("keyword-group-modal");
    if (modal) modal.classList.add("hidden");
}

async function saveKeywordGroup(e) {
    e.preventDefault();
    const name = document.getElementById("kw-name").value.trim();
    const positive = document.getElementById("kw-positive").value.split(",").map(s => s.trim()).filter(Boolean);
    const negative = document.getElementById("kw-negative").value.split(",").map(s => s.trim()).filter(Boolean);
    const priority_weight = parseFloat(document.getElementById("kw-weight").value) || 1.0;
    const color = document.getElementById("kw-color").value || "#3B82F6";

    try {
        const res = await fetch("/api/v1/keywords", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, positive_keywords: positive, negative_keywords: negative, priority_weight, color })
        });

        if (res.ok) {
            closeKeywordModal();
            loadKeywords();
        } else {
            const err = await res.json();
            alert(`Error: ${err.detail || 'Failed to create keyword group'}`);
        }
    } catch (e) {
        console.error("Save keyword group error:", e);
    }
}

async function deleteKeywordGroup(id) {
    if (confirm("Are you sure you want to delete this keyword group?")) {
        await fetch(`/api/v1/keywords/${id}`, { method: "DELETE" });
        loadKeywords();
    }
}
