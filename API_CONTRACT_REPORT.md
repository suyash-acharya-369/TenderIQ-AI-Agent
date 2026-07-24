# TenderIQ AI — API Contract Report

---

## 1. Authentication & User Management
- `POST /api/v1/auth/login` — Authenticate user, return JWT access token, refresh token, and user payload.
- `POST /api/v1/auth/register` — Register new user account.
- `POST /api/v1/auth/refresh` — Rotate refresh token for new access token.
- `GET /api/v1/auth/me` — Get current authenticated user profile.
- `GET /api/v1/users` — List all registered users (Administrator only).
- `POST /api/v1/users` — Create user account (Administrator only).
- `PUT /api/v1/users/{id}` — Update user profile/role/status (Administrator only).
- `DELETE /api/v1/users/{id}` — Delete user account (Administrator only).

---

## 2. Command Center & Dashboard
- `GET /api/v1/dashboard/kpis` — Aggregate metrics: Total opportunities, High priority, Closing soon, Pipeline value INR.
- `GET /api/v1/dashboard/recent-crawls` — Retrieve recent portal crawl history runs.
- `GET /api/v1/dashboard/recent-ai` — Retrieve top recent AI analyzed tenders.
- `GET /api/v1/dashboard/distribution` — Global/regional tender distribution by country and total value.
- `GET /api/v1/dashboard/trends` — Priority match bucket distribution.
- `GET /api/v1/dashboard/live-feed` — Real-time indexed tender activity feed.
- `POST /api/v1/dashboard/ai-brief` — Produce executive briefing via OpenRouter AI.

---

## 3. Tender Intelligence
- `GET /api/v1/tenders` — Search and filter tenders (`q`, `country`, `sector`, `status`, `min_score`, `min_budget`, `limit`, `offset`).
- `GET /api/v1/tenders/{id}` — Retrieve detailed tender profile with attachments and version history.
- `POST /api/v1/tenders/{id}/run-ai` — Trigger live OpenRouter AI summary, risk analysis, and match score computation.

---

## 4. Source Manager & Crawlers
- `GET /api/v1/sources` — List all procurement portals.
- `POST /api/v1/sources` — Add new procurement portal.
- `PUT /api/v1/sources/{id}` — Update procurement portal parameters/credentials.
- `DELETE /api/v1/sources/{id}` — Delete procurement portal source.
- `POST /api/v1/sources/{id}/run-crawl` — Execute real web crawl & opportunity extraction.
- `POST /api/v1/sources/{id}/toggle-pause` — Toggle source status between active and paused.

---

## 5. Keyword Manager
- `GET /api/v1/keywords` — List keyword groups.
- `POST /api/v1/keywords` — Create keyword group (positive, negative, mandatory, weight, color).
- `PUT /api/v1/keywords/{id}` — Update keyword group parameters.
- `DELETE /api/v1/keywords/{id}` — Delete keyword group.

---

## 6. Organizations
- `GET /api/v1/organizations` — List procurement organizations.
- `GET /api/v1/organizations/{id}` — Get organization profile.
- `GET /api/v1/organizations/{id}/tenders` — Get all tenders published by an organization.
- `POST /api/v1/organizations` — Create organization profile.
- `PUT /api/v1/organizations/{id}` — Update organization profile.

---

## 7. System Administration & Analytics
- `GET /api/v1/admin/crawl-history` — Admin portal crawl execution logs.
- `GET /api/v1/admin/queue-status` — Background job queue monitoring.
- `GET /api/v1/admin/ai-costs` — OpenRouter AI token consumption & cost tracking.
- `GET /api/v1/admin/audit-logs` — Platform audit event trail.
- `GET /api/v1/settings` — Admin system settings (Administrator only).
- `POST /api/v1/settings` — Update system settings & persist to `.env` (Administrator only).
- `GET /api/v1/prompts` — AI prompt templates (Administrator only).
- `PUT /api/v1/prompts/{id}` — Update prompt template (Administrator only).
- `GET /api/v1/health` — System CPU, RAM, Disk, DB, and AI status.
- `GET /api/v1/analytics/export/csv` — Export tender report as CSV.
- `GET /api/v1/analytics/export/excel` — Export tender report as Excel (`openpyxl`).
- `GET /api/v1/analytics/export/pdf` — Export executive summary as PDF (`reportlab`).
