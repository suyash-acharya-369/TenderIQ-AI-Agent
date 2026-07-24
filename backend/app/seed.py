import os
from datetime import datetime, timezone, timedelta
from backend.app.database.session import SessionLocal, engine, Base
from backend.app.models.user import User
from backend.app.models.source import Source, CrawlHistory
from backend.app.models.keyword import KeywordGroup
from backend.app.models.tender import Tender, TenderAttachment, TenderVersion, Organization
from backend.app.models.ai import PromptTemplate
from backend.app.utils.security import hash_password

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Initial Admin User
        admin_email = "admin@tenderiq.ai"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("Admin123!"),
                full_name="System Administrator",
                role="Administrator",
                is_active=True,
                is_verified=True
            )
            db.add(admin)
            db.commit()
            print("Seeded default administrator user: admin@tenderiq.ai / Admin123!")

        # 2. Seed 10 Configured Production Sources
        production_portals = [
            {
                "name": "Government e-Marketplace (GeM)",
                "base_url": "https://gem.gov.in",
                "search_url": "https://gem.gov.in/search?q=lms+elearning",
                "connector_type": "Browser Automation (Playwright)",
                "tender_selector": ".variant-card, .bid-card",
                "priority": "P1 - Critical"
            },
            {
                "name": "Central Public Procurement Portal (CPPP)",
                "base_url": "https://eprocure.gov.in",
                "search_url": "https://eprocure.gov.in/cppp/latestactivetenders",
                "connector_type": "Public Website",
                "tender_selector": "#activeTenders table tr",
                "priority": "P1 - Critical"
            },
            {
                "name": "BidAssist",
                "base_url": "https://bidassist.com",
                "search_url": "https://bidassist.com/tenders/search?q=elearning",
                "connector_type": "Public Website",
                "tender_selector": ".tender-card",
                "priority": "P2 - High"
            },
            {
                "name": "TenderTiger",
                "base_url": "https://tendertiger.com",
                "search_url": "https://tendertiger.com/tenders/search",
                "connector_type": "Public Website",
                "tender_selector": ".tender-row",
                "priority": "P2 - High"
            },
            {
                "name": "NGOBox",
                "base_url": "https://ngobox.org",
                "search_url": "https://ngobox.org/RFP-tenders",
                "connector_type": "Public Website",
                "tender_selector": ".rfp-item, .job-item",
                "priority": "P1 - Critical"
            },
            {
                "name": "CSRBOX",
                "base_url": "https://csrbox.org",
                "search_url": "https://csrbox.org/India_CSR_projects_listing",
                "connector_type": "Public Website",
                "tender_selector": ".project-card",
                "priority": "P2 - High"
            },
            {
                "name": "DevelopmentAid",
                "base_url": "https://developmentaid.org",
                "search_url": "https://developmentaid.org/api/v2/tenders",
                "connector_type": "REST API",
                "tender_selector": "json",
                "priority": "P1 - Critical"
            },
            {
                "name": "World Bank Project Procurement",
                "base_url": "https://projects.worldbank.org",
                "search_url": "https://search.worldbank.org/api/v2/procurement",
                "connector_type": "REST API",
                "tender_selector": "json",
                "priority": "P1 - Critical"
            },
            {
                "name": "United Nations Global Marketplace (UNGM)",
                "base_url": "https://ungm.org",
                "search_url": "https://www.ungm.org/Public/Notice/Feed/Rss",
                "connector_type": "RSS",
                "tender_selector": "rss",
                "priority": "P1 - Critical"
            },
            {
                "name": "DevNetJobs",
                "base_url": "https://devnetjobs.org",
                "search_url": "https://devnetjobs.org/tenders.aspx",
                "connector_type": "Public Website",
                "tender_selector": ".job-table tr",
                "priority": "P2 - High"
            }
        ]

        for portal in production_portals:
            existing = db.query(Source).filter(Source.name == portal["name"]).first()
            if existing:
                existing.base_url = portal["base_url"]
                existing.search_url = portal["search_url"]
                existing.connector_type = portal["connector_type"]
                existing.status = "active"
                existing.health_status = "Healthy"
            else:
                src = Source(
                    name=portal["name"],
                    base_url=portal["base_url"],
                    search_url=portal["search_url"],
                    connector_type=portal["connector_type"],
                    tender_selector=portal["tender_selector"],
                    frequency="daily",
                    priority=portal["priority"],
                    status="active",
                    health_status="Healthy",
                    last_crawl=datetime.now(timezone.utc) - timedelta(hours=2),
                    next_crawl=datetime.now(timezone.utc) + timedelta(hours=22)
                )
                db.add(src)
        db.commit()
        print("Seeded 10 production procurement portals.")

        # 3. Seed 10 Targeted Keyword Groups
        production_keywords = [
            {
                "name": "Education",
                "positive": ["Education", "School Education", "Higher Education", "University", "College", "Vocational Education", "Skill Development", "Teacher Training", "Faculty Development", "Education Technology", "EdTech"],
                "negative": ["Hardware Maintenance", "Construction"],
                "mandatory": ["Education"],
                "priority_weight": 1.5,
                "color": "#8B5CF6"
            },
            {
                "name": "Learning Platforms",
                "positive": ["LMS", "Learning Management System", "Learning Platform", "Learning Portal", "Learning Experience Platform", "LXP", "Moodle", "Canvas LMS", "Blackboard", "Open edX", "TalentLMS"],
                "negative": ["Civil Works"],
                "mandatory": ["System"],
                "priority_weight": 1.5,
                "color": "#3B82F6"
            },
            {
                "name": "Digital Learning",
                "positive": ["E-Learning", "eLearning", "Online Learning", "Digital Learning", "Virtual Learning", "Distance Learning", "Blended Learning", "Interactive Learning", "Digital Course"],
                "negative": ["Catering", "Janitorial"],
                "mandatory": ["Learning"],
                "priority_weight": 1.4,
                "color": "#10B981"
            },
            {
                "name": "Content Development",
                "positive": ["E-Content", "Digital Content", "Learning Content", "Content Development", "Instructional Design", "Curriculum Design", "Content Authoring", "Storyboard", "Assessment Development", "Question Bank", "Courseware"],
                "negative": ["Security Guards"],
                "mandatory": ["Content"],
                "priority_weight": 1.3,
                "color": "#F59E0B"
            },
            {
                "name": "Authoring Tools",
                "positive": ["Articulate Storyline", "Storyline", "Rise 360", "Adobe Captivate", "Lectora", "iSpring", "Elucidat", "Adapt Learning", "SCORM", "xAPI", "Tin Can API", "AICC"],
                "negative": [],
                "mandatory": [],
                "priority_weight": 1.4,
                "color": "#EC4899"
            },
            {
                "name": "Multimedia",
                "positive": ["Animation", "2D Animation", "3D Animation", "Motion Graphics", "Educational Video", "Interactive Video", "Voice Over", "Infographic"],
                "negative": ["CCTV Camera"],
                "mandatory": [],
                "priority_weight": 1.2,
                "color": "#6366F1"
            },
            {
                "name": "Digital Education",
                "positive": ["Digital Classroom", "Smart Classroom", "ICT Education", "Education Portal", "Student Portal", "Teacher Portal", "Academic ERP", "Campus Management"],
                "negative": [],
                "mandatory": [],
                "priority_weight": 1.3,
                "color": "#14B8A6"
            },
            {
                "name": "Government Initiatives",
                "positive": ["NEP", "National Education Policy", "NSQF", "Skill India", "Digital India", "PM eVIDYA", "SWAYAM", "DIKSHA", "Samagra Shiksha", "NCERT", "CBSE", "AICTE", "UGC", "IGNOU"],
                "negative": [],
                "mandatory": [],
                "priority_weight": 1.5,
                "color": "#EF4444"
            },
            {
                "name": "Training",
                "positive": ["Corporate Training", "Capacity Building", "Training Program", "Training Portal", "Learning Academy", "Professional Development", "Upskilling", "Reskilling"],
                "negative": ["Driver Training"],
                "mandatory": ["Training"],
                "priority_weight": 1.2,
                "color": "#84CC16"
            },
            {
                "name": "AI in Education",
                "positive": ["AI Learning", "Adaptive Learning", "Generative AI", "AI Tutor", "Learning Analytics", "Personalized Learning", "Assessment Engine"],
                "negative": [],
                "mandatory": [],
                "priority_weight": 1.6,
                "color": "#A855F7"
            }
        ]

        for kg in production_keywords:
            existing = db.query(KeywordGroup).filter(KeywordGroup.name == kg["name"]).first()
            if existing:
                existing.positive_keywords = kg["positive"]
                existing.negative_keywords = kg["negative"]
                existing.mandatory_keywords = kg["mandatory"]
                existing.priority_weight = kg["priority_weight"]
                existing.color = kg["color"]
            else:
                group = KeywordGroup(
                    name=kg["name"],
                    positive_keywords=kg["positive"],
                    negative_keywords=kg["negative"],
                    mandatory_keywords=kg["mandatory"],
                    priority_weight=kg["priority_weight"],
                    color=kg["color"],
                    status="active"
                )
                db.add(group)
        db.commit()
        print("Seeded 10 production domain keyword groups.")

        # 4. Seed Initial Prompt Templates
        prompts = [
            ("Summary", "Executive Summary", "Analyze the following tender text and generate a structured JSON summary covering Scope, Deliverables, Eligibility, Technical Requirements, Financial Requirements, Required Documents, and Deadline Summary."),
            ("Risk", "Risk Analysis", "Evaluate technical, financial, and operational risks for bidding on this opportunity."),
            ("Scoring", "Bid Match Scoring", "Compute relevance score (0-100) based on company capabilities in E-learning, LMS development, SCORM content, and skill training."),
            ("Notification", "Alert Formatter", "Format high-priority tender alert message for Email and WhatsApp delivery.")
        ]
        for name, task_type, text in prompts:
            existing = db.query(PromptTemplate).filter(PromptTemplate.name == name).first()
            if not existing:
                pt = PromptTemplate(name=name, task_type=task_type, template_text=text, provider="openai")
                db.add(pt)
        db.commit()

        # 5. Seed Organizations & Verified Tenders across ALL 10 Production Portals
        sources = {s.name: s for s in db.query(Source).all()}

        organizations = [
            ("Ministry of Education, Govt of India", "India", "Government"),
            ("UNESCO / UNGM Secretariat", "International", "International"),
            ("World Bank Group", "International", "International"),
            ("National Skill Development Corporation (NSDC)", "India", "Government"),
            ("ADB DevelopmentAid Portal", "Asia", "International"),
            ("NITI Aayog, Govt of India", "India", "Government")
        ]

        org_db_map = {}
        for o_name, o_country, o_sector in organizations:
            org = db.query(Organization).filter(Organization.name == o_name).first()
            if not org:
                org = Organization(name=o_name, country=o_country, sector=o_sector, website=f"https://{o_name.lower().replace(' ', '')}.org")
                db.add(org)
                db.commit()
            org_db_map[o_name] = org

        seeded_tenders = [
            {
                "number": "GEM/2026/B/892341",
                "title": "Development of Next-Gen AI-Powered LMS & Interactive SCORM Content for National Skill Portal",
                "source_name": "Government e-Marketplace (GeM)",
                "org_name": "Ministry of Education, Govt of India",
                "budget": 8500000.0,
                "country": "India",
                "scope": "Design, build, deploy, and maintain a high-concurrency Cloud LMS supporting 500k active students. Develop 200 hours of 4-Quadrant SCORM 1.2/2004 interactive modules in Articulate Storyline and Rise 360 with AI Tutor adaptive learning.",
                "summary": "High-value strategic opportunity matching 95% of core e-learning, LMS development, and AI in Education capabilities.",
                "recommendation": "Bid",
                "win_prob": 94.0,
                "score": 95.5
            },
            {
                "number": "UNGM-RFP-2026-9921",
                "title": "Global Digital Education & LMS Platform for UNESCO Capacity Building",
                "source_name": "United Nations Global Marketplace (UNGM)",
                "org_name": "UNESCO / UNGM Secretariat",
                "budget": 1200000.0,
                "country": "Global",
                "scope": "Development of an internationalized multi-lingual Open edX / Moodle LMS platform with AI Learning Analytics and SCORM content packaging for 45 developing nations.",
                "summary": "Global UN tender for LMS platform deployment and instructional design content development.",
                "recommendation": "Bid",
                "win_prob": 91.0,
                "score": 93.0
            },
            {
                "number": "WB-PROC-2026-041",
                "title": "Digital Transformation & EdTech Capacity Building Project",
                "source_name": "World Bank Project Procurement",
                "org_name": "World Bank Group",
                "budget": 2500000.0,
                "country": "International",
                "scope": "Procurement of digital classroom software, teacher training LMS, and 3D educational video animation modules for national curriculum reform.",
                "summary": "Multi-year World Bank funded EdTech project covering digital learning, LMS platforms, and teacher training.",
                "recommendation": "Bid",
                "win_prob": 88.0,
                "score": 91.5
            },
            {
                "number": "CPPP/2026/ED/4412",
                "title": "Development of Smart Classroom E-Content & Digital Learning Portal for State Schools",
                "source_name": "Central Public Procurement Portal (CPPP)",
                "org_name": "Ministry of Education, Govt of India",
                "budget": 4500000.0,
                "country": "India",
                "scope": "Creation of 2D/3D animated e-content for Grades 6-12 aligned with NEP 2020. Deployment of cloud-hosted Student Portal and Assessment Engine.",
                "summary": "State-level NEP 2020 digital content and smart classroom portal development.",
                "recommendation": "Bid",
                "win_prob": 90.0,
                "score": 92.0
            },
            {
                "number": "BA-2026-8819",
                "title": "Corporate E-Learning Portal & Articulate Storyline Content Authoring",
                "source_name": "BidAssist",
                "org_name": "National Skill Development Corporation (NSDC)",
                "budget": 3200000.0,
                "country": "India",
                "scope": "Custom Rise 360 and Articulate Storyline interactive module creation for skill certification programs and capacity building.",
                "summary": "Corporate skill development tender focusing on authoring tools and SCORM compliance.",
                "recommendation": "Bid",
                "win_prob": 89.0,
                "score": 89.5
            },
            {
                "number": "NGO-RFP-2026-104",
                "title": "Community Upskilling Portal & Interactive Video Content",
                "source_name": "NGOBox",
                "org_name": "NITI Aayog, Govt of India",
                "budget": 1800000.0,
                "country": "India",
                "scope": "Development of mobile-first offline-capable learning app and video content in 8 regional languages.",
                "summary": "Community digital education and upskilling training portal.",
                "recommendation": "Consider",
                "win_prob": 84.0,
                "score": 86.0
            },
            {
                "number": "DEVAID-2026-551",
                "title": "International Vocational E-Learning & Faculty Training Program",
                "source_name": "DevelopmentAid",
                "org_name": "ADB DevelopmentAid Portal",
                "budget": 950000.0,
                "country": "Asia",
                "scope": "Implementation of blended virtual learning LMS for vocational institutes and faculty development.",
                "summary": "International development bank funded vocational training and LMS.",
                "recommendation": "Bid",
                "win_prob": 87.0,
                "score": 88.0
            },
            {
                "number": "CSR-2026-092",
                "title": "Digital Saksharta Initiative - E-Content & Teacher Training",
                "source_name": "CSRBOX",
                "org_name": "Ministry of Education, Govt of India",
                "budget": 2100000.0,
                "country": "India",
                "scope": "CSR funded initiative for digital literacy, teacher training portal, and NEP curriculum digitized modules.",
                "summary": "CSR digital literacy initiative with teacher portal and content development.",
                "recommendation": "Consider",
                "win_prob": 85.0,
                "score": 87.5
            },
            {
                "number": "TT-2026-7731",
                "title": "Campus Management & Academic ERP System Implementation",
                "source_name": "TenderTiger",
                "org_name": "Ministry of Education, Govt of India",
                "budget": 5000000.0,
                "country": "India",
                "scope": "Implementation of student portal, learning analytics engine, and academic campus management ERP for 20 polytechnic institutes.",
                "summary": "Higher education campus management and ERP software.",
                "recommendation": "Consider",
                "win_prob": 82.0,
                "score": 85.0
            },
            {
                "number": "DEVNET-2026-309",
                "title": "Distance Learning Portal & SCORM Content Development",
                "source_name": "DevNetJobs",
                "org_name": "UNESCO / UNGM Secretariat",
                "budget": 750000.0,
                "country": "Global",
                "scope": "Creation of SCORM 1.2 interactive modules and LMS portal for international development practitioners.",
                "summary": "Global NGO distance learning and SCORM content creation.",
                "recommendation": "Bid",
                "win_prob": 89.0,
                "score": 90.0
            }
        ]

        for item in seeded_tenders:
            existing = db.query(Tender).filter(Tender.tender_number == item["number"]).first()
            src = sources.get(item["source_name"])
            org = org_db_map.get(item["org_name"])

            if not existing:
                t = Tender(
                    tender_number=item["number"],
                    title=item["title"],
                    organization_id=org.id if org else None,
                    source_id=src.id if src else None,
                    country=item["country"],
                    sector="Education",
                    budget=item["budget"],
                    currency="INR" if item["country"] == "India" else "USD",
                    publication_date=datetime.now(timezone.utc) - timedelta(days=1),
                    submission_deadline=datetime.now(timezone.utc) + timedelta(days=20),
                    status="Active",
                    access_status="Verified",
                    official_link=src.search_url if src else "https://gem.gov.in",
                    scope_of_work=item["scope"],
                    deliverables="1. Production Cloud System\n2. SCORM Content Packages\n3. Source Code & Docs",
                    eligibility_criteria="Minimum 3 years experience in E-Learning, LMS, or EdTech software development.",
                    technical_requirements="Moodle / React / Python LMS, SCORM 1.2/2004, Articulate Storyline / Rise 360 compatible.",
                    financial_requirements="Positive net worth for last 3 financial years.",
                    required_documents="1. Technical RFP Proposal\n2. Commercial Bid\n3. Certificate of Incorporation",
                    ai_summary=item["summary"],
                    risk_analysis="Standard execution risk with fixed 6-month deadline.",
                    bid_recommendation=item["recommendation"],
                    winning_probability=item["win_prob"],
                    estimated_team="1 ID Lead, 3 Developers, 1 QA",
                    estimated_duration="6 Months",
                    keyword_score=item["score"],
                    semantic_score=item["score"] - 1.0,
                    ai_score=item["score"] + 1.0,
                    priority_score=95.0,
                    overall_match_score=item["score"]
                )
                db.add(t)
                db.commit()

                # Attachment
                att = TenderAttachment(
                    tender_id=t.id,
                    file_name=f"RFP_Specification_{t.tender_number.replace('/', '_')}.pdf",
                    file_type="PDF",
                    file_path=f"./storage/rfp_{t.id}.pdf",
                    file_size_bytes=1850000,
                    parsed_content=f"Official RFP specifications for {t.title}. Scope: {t.scope_of_work}"
                )
                db.add(att)
                db.commit()

        print("Database seeding completed successfully for all 10 portals & 10 keyword groups!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
