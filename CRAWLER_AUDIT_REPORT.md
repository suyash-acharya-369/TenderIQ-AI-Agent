# CRAWLER AUDIT REPORT — TENDERIQ AI PLATFORM

**Audit Date**: July 24, 2026  
**Auditor**: Antigravity AI Engineering  
**Scope**: End-to-End Crawler Pipeline, Connectors, Deduplication & Storage Architecture  

---

## 1. Executive Summary

The backend crawler pipeline has been thoroughly audited and upgraded. The engine now operates a **keyword-driven multi-search framework** across 10 administrator-approved procurement portals. Instead of relying solely on homepage crawling, the engine dynamically constructs targeted query requests for each active domain keyword group (e.g. *E-Learning*, *LMS*, *Digital Content*, *Articulate Storyline*, *AI in Education*).

---

## 2. Crawler Pipeline Architecture

```
[Administrator Keyword Groups] 
       ↓
[Connector Selection (Generic, RSS, API, Playwright)] 
       ↓
[Portal Target Construction (Dynamic Query Parameters)] 
       ↓
[HTTP Fetching / Browser Rendering (3-Retry Backoff)] 
       ↓
[HTML Parsing & JSON Extraction] 
       ↓
[Deduplication Check (Tender No, Title, URL)] 
       ↓
[PDF Download & OCR Text Extraction (document_processor.py)] 
       ↓
[OpenRouter AI Analysis (GPT-4o Mini Summary & Risk Analysis)] 
       ↓
[Match Score Calculation (Keyword + Vector Semantic Similarity)] 
       ↓
[Database Storage (Tender, TenderAttachment, CrawlHistory)] 
       ↓
[Live UI Synchronization (Tender Intelligence & Dashboard)]
```

---

## 3. Crawler Engine Operational Metrics

| Metric | Pre-Audit | Post-Audit Status |
| :--- | :--- | :--- |
| **Search Strategy** | Homepage static crawl | **Keyword-driven multi-search iteration** |
| **PDF Extraction** | Unhandled | **Automatic download to `./storage/` with text extraction** |
| **AI Integration** | Fixed mock fallback | **OpenRouter API (`openai/gpt-4o-mini`) + fallback** |
| **Retry Logic** | None (failed on timeout) | **3-attempt exponential backoff retries** |
| **Audit Logging** | Unregistered | **Logged in `CrawlHistory` with URLs, duration, and error tracebacks** |

---

## 4. Key Improvements & Fixes

1. **Multi-Connector Support**: Verified operational health across `GenericConnector` (BeautifulSoup/HTTPX), `RSSConnector`, `APIConnector`, and `PlaywrightConnector`.
2. **Deduplication & Corrigenda Tracking**: Deduplicates by tender number, title, and official URL. Re-crawled tenders with updated terms trigger version history records (`TenderVersion`).
3. **Error Resilience**: Failed HTTP requests gracefully retry up to 3 times before setting portal `health_status = "Unhealthy"`.
