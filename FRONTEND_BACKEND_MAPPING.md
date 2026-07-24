# TenderIQ AI — Frontend ↔ Backend Mapping Report

---

## 1. Unified Website Single Server Architecture
The entire platform runs as a **single website served on `http://127.0.0.1:8000`** powered by FastAPI.

---

## 2. Page-to-API Data Mapping Matrix

| Page Route | Template HTML Path | Client Script | Backend APIs Consumed | Interactive Controls & Modals |
|---|---|---|---|---|
| `/login` | `login_tenderiq_ai/code.html` | `auth.js` | `POST /api/v1/auth/login` | Login form submission, authentication token storage in localStorage. |
| `/` (Dashboard) | `dashboard_tenderiq_ai/code.html` | `app.js`, `dashboard.js` | `GET /api/v1/dashboard/kpis`<br>`GET /api/v1/dashboard/distribution`<br>`GET /api/v1/dashboard/trends`<br>`GET /api/v1/dashboard/live-feed`<br>`POST /api/v1/dashboard/ai-brief` | Live pulse refresh (10s), real-time web crawl trigger, OpenRouter Executive AI Brief modal, global search bar. |
| `/opportunities` | `opportunities_tenderiq_ai/code.html` | `app.js`, `opportunities.js` | `GET /api/v1/tenders`<br>`GET /api/v1/tenders?q=...`<br>`POST /api/v1/tenders/{id}/run-ai` | Live search input filtering, Tender Details quick modal, OpenRouter AI Summarizer button. |
| `/opportunity-details` | `opportunity_details_tenderiq_ai/code.html` | `app.js`, `opportunities.js` | `GET /api/v1/tenders/{id}`<br>`POST /api/v1/tenders/{id}/run-ai` | Dynamic DOM population for tender title, scope, match score, requirements, attachments list, corrigendum timeline, and AI re-run. |
| `/sources` | `source_manager_tenderiq_ai/code.html` | `app.js`, `sources.js` | `GET /api/v1/sources`<br>`POST /api/v1/sources`<br>`POST /api/v1/sources/{id}/run-crawl`<br>`POST /api/v1/sources/{id}/toggle-pause`<br>`DELETE /api/v1/sources/{id}` | Source table list, Add Source Portal modal form, manual crawl button, pause/resume button, delete source. |
| `/keywords` | `keyword_manager_tenderiq_ai/code.html` | `app.js`, `keywords.js` | `GET /api/v1/keywords`<br>`POST /api/v1/keywords`<br>`DELETE /api/v1/keywords/{id}` | Keyword group grid, Create Keyword Group modal form, weight badges, color indicators, group deletion. |
| `/ai-analysis` | `ai_analysis_tenderiq_ai/code.html` | `app.js`, `ai_analysis.js` | `GET /api/v1/tenders`<br>`POST /api/v1/tenders/{id}/run-ai` | Tender selection dropdown, live AI summary view, risk analysis display, interactive OpenRouter re-run button. |
| Settings Modal | (Global Modal in `app.js`) | `app.js` | `GET /api/v1/settings`<br>`POST /api/v1/settings` | OpenAI/OpenRouter API key update, SMTP email server setup, Meta WhatsApp token configuration with `.env` file persistence. |
