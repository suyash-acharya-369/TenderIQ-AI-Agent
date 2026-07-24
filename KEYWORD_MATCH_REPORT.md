# KEYWORD MATCH & AI RELEVANCE REPORT

**Audit Date**: July 24, 2026  
**Module**: TenderIQ AI Relevance Engine & Keyword Ecosystem  

---

## 1. Domain Keyword Groups Summary

The TenderIQ AI platform operates **10 configured domain keyword groups**. Every discovered tender is evaluated against these keyword groups using exact term matching, negative filter exclusion, and vector semantic similarity.

| Keyword Group Name | Priority Weight | Key Positive Terms | Negative Filter Terms | Color Code |
| :--- | :---: | :--- | :--- | :---: |
| **Education** | 1.5 | Education, Higher Education, EdTech, School, Skill Development | Hardware Maintenance, Construction | `#8B5CF6` |
| **Learning Platforms** | 1.5 | LMS, Learning Management System, Moodle, Canvas LMS, Open edX | Civil Works | `#3B82F6` |
| **Digital Learning** | 1.4 | E-Learning, Online Learning, Virtual Learning, Blended Learning | Catering, Janitorial | `#10B981` |
| **Content Development** | 1.3 | E-Content, Digital Content, Instructional Design, Storyboard | Security Guards | `#F59E0B` |
| **Authoring Tools** | 1.4 | Articulate Storyline, Rise 360, Adobe Captivate, SCORM, xAPI | None | `#EC4899` |
| **Multimedia** | 1.2 | 2D Animation, 3D Animation, Motion Graphics, Educational Video | CCTV Camera | `#6366F1` |
| **Digital Education** | 1.3 | Digital Classroom, Smart Classroom, ICT Education, Student Portal | None | `#14B8A6` |
| **Government Initiatives** | 1.5 | NEP, Skill India, Digital India, PM eVIDYA, SWAYAM, DIKSHA | None | `#EF4444` |
| **Training** | 1.2 | Corporate Training, Capacity Building, Upskilling, Reskilling | Driver Training | `#84CC16` |
| **AI in Education** | 1.6 | AI Learning, Adaptive Learning, AI Tutor, Learning Analytics | None | `#A855F7` |

---

## 2. Relevance Scoring Formula

Every tender receives a multi-dimensional match score computed as follows:

$$\text{Overall Match Score} = 0.35 \times S_{\text{keyword}} + 0.35 \times S_{\text{semantic}} + 0.20 \times S_{\text{ai}} + 0.10 \times P_{\text{boost}}$$

Where:
- $S_{\text{keyword}}$: Percentage of positive keywords present in Title, Scope, and PDF Text minus negative keyword penalties.
- $S_{\text{semantic}}$: Vector cosine similarity / Jaccard set similarity between tender scope and company capabilities.
- $S_{\text{ai}}$: OpenRouter AI (`openai/gpt-4o-mini`) structural alignment score.
- $P_{\text{boost}}$: Priority weight multiplier for high-value groups (*AI in Education*, *NEP / Skill India*).

---

## 3. Dynamic Keyword Synchronization Verification

- **Real-Time Synchronizations**: Adding or modifying a Keyword Group in the **Keyword Manager** (`/keywords`) immediately updates filter dropdowns in **Tender Intelligence** (`/opportunities`) and recalculates relevance scores on subsequent crawl runs.
