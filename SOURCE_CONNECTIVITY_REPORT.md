# SOURCE CONNECTIVITY REPORT — PRODUCTION PROCUREMENT PORTALS

**Verification Date**: July 24, 2026  
**Target Portals**: 10 Administrator-Approved Sources  

---

## 1. Source Connectivity Status Table

| Portal Name | Connector Type | Base Search URL | Health Status | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **Government e-Marketplace (GeM)** | Playwright / HTTPX | `https://gem.gov.in/search?q=lms+elearning` | **Healthy** | Verified (HTTP 200) |
| **Central Public Procurement Portal (CPPP)** | Public Website | `https://eprocure.gov.in/cppp/latestactivetenders` | **Healthy** | Verified (HTTP 200) |
| **BidAssist** | Public Website | `https://bidassist.com/tenders/search?q=elearning` | **Healthy** | Verified (HTTP 200) |
| **TenderTiger** | Public Website | `https://tendertiger.com/tenders/search` | **Healthy** | Verified (HTTP 200) |
| **NGOBox** | Public Website | `https://ngobox.org/RFP-tenders` | **Healthy** | Verified (HTTP 200) |
| **CSRBOX** | Public Website | `https://csrbox.org/India_CSR_projects_listing` | **Healthy** | Verified (HTTP 200) |
| **DevelopmentAid** | REST API | `https://developmentaid.org/api/v2/tenders` | **Healthy** | Verified (JSON 200) |
| **World Bank Project Procurement** | REST API | `https://search.worldbank.org/api/v2/procurement` | **Healthy** | Verified (JSON 200) |
| **United Nations Global Marketplace (UNGM)** | RSS | `https://www.ungm.org/Public/Notice/Feed/Rss` | **Healthy** | Verified (XML 200) |
| **DevNetJobs** | Public Website | `https://devnetjobs.org/tenders.aspx` | **Healthy** | Verified (HTTP 200) |

---

## 2. Connector Retry & Health Monitoring Protocol

- **Timeout Threshold**: 30 seconds per request.
- **Max Retries**: 3 attempts with exponential backoff ($2^n$ seconds).
- **Fallback Protocol**: Headless Playwright browser automation falls back gracefully to `HTTPX` + `BeautifulSoup` when headless browser binaries are uninstalled in lightweight container environments.
- **Health State Transition**: Source marked `Warning` after 2 consecutive timeouts and `Unhealthy` after 3 consecutive failures.

---

## 3. Administrator Actions Exposed in UI

Through the **Source Management** page (`/sources`), administrators can:
- Toggle portal **Enable / Disable**.
- Modify CSS selectors, pagination selectors, and search URLs.
- Trigger **Run Manual Crawl** with instantaneous progress toasts.
- Inspect detailed **Crawl Execution Logs** (`CrawlHistory`).
