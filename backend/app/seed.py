from datetime import datetime, timezone, timedelta
from backend.app.database.session import SessionLocal, Base, engine
from backend.app.models.user import User
from backend.app.models.source import Source
from backend.app.models.keyword import KeywordGroup
from backend.app.models.tender import Tender, Organization, TenderAttachment, TenderVersion
from backend.app.models.ai import PromptTemplate
from backend.app.utils.security import hash_password

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Admin User
        admin = db.query(User).filter(User.email == "admin@tenderiq.ai").first()
        if not admin:
            admin = User(
                email="admin@tenderiq.ai",
                hashed_password=hash_password("Admin@123456"),
                full_name="Administrator",
                role="Administrator",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("Seeded admin user: admin@tenderiq.ai / Admin@123456")

        # 2. Seed 25 Procurement Portals
        initial_portals = [
            {"name": "GeM (Government e-Marketplace)", "website_url": "https://gem.gov.in", "country": "India", "category": "Government", "connector_type": "Public"},
            {"name": "CPPP (Central Public Procurement Portal)", "website_url": "https://eprocure.gov.in/cppp/", "country": "India", "category": "Government", "connector_type": "Public"},
            {"name": "Tender Tiger", "website_url": "https://www.tendertiger.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "Tender247", "website_url": "https://www.tender247.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "TenderMines", "website_url": "https://www.tendermines.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "TenderDetail", "website_url": "https://www.tenderdetail.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "Skill India Tenders", "website_url": "https://www.skillindia.gov.in", "country": "India", "category": "Government", "connector_type": "Public"},
            {"name": "Skillspedia", "website_url": "https://skillspedia.in", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "SkillReporter", "website_url": "https://skillreporter.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "NGOBOX", "website_url": "https://ngobox.org", "country": "India", "category": "NGOs", "connector_type": "Public"},
            {"name": "CSRBOX", "website_url": "https://csrbox.org", "country": "India", "category": "NGOs", "connector_type": "Public"},
            {"name": "DevNetJobs", "website_url": "https://www.devnetjobs.org", "country": "International", "category": "NGOs", "connector_type": "Public"},
            {"name": "TendersOnTime", "website_url": "https://www.tendersontime.com", "country": "International", "category": "Corporate", "connector_type": "Public"},
            {"name": "BidAssist", "website_url": "https://bidassist.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "TheTenders", "website_url": "https://thetenders.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "TenderNews", "website_url": "https://www.tendernews.com", "country": "International", "category": "Corporate", "connector_type": "Public"},
            {"name": "TenderSniper", "website_url": "https://tendersniper.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "TendersKhoj", "website_url": "https://tenderskhoj.com", "country": "India", "category": "Corporate", "connector_type": "Public"},
            {"name": "World Bank Procurement", "website_url": "https://projects.worldbank.org/en/projects-operations/procurement", "country": "International", "category": "International", "connector_type": "API"},
            {"name": "DevelopmentAid", "website_url": "https://www.developmentaid.org", "country": "International", "category": "International", "connector_type": "Public"},
            {"name": "GlobalTenders", "website_url": "https://www.globaltenders.com", "country": "International", "category": "International", "connector_type": "Public"},
            {"name": "TenderImpulse", "website_url": "https://www.tenderimpulse.com", "country": "International", "category": "International", "connector_type": "Public"},
            {"name": "MP eTender", "website_url": "https://mptenders.gov.in", "country": "India", "category": "Government", "connector_type": "Public"},
            {"name": "iGOT Karmayogi", "website_url": "https://igotkarmayogi.gov.in", "country": "India", "category": "Government", "connector_type": "Public"},
            {"name": "NCVET Procurement", "website_url": "https://ncvet.gov.in", "country": "India", "category": "Government", "connector_type": "Public"},
        ]

        for portal in initial_portals:
            existing = db.query(Source).filter(Source.name == portal["name"]).first()
            if not existing:
                src = Source(
                    name=portal["name"],
                    website_url=portal["website_url"],
                    country=portal["country"],
                    category=portal["category"],
                    connector_type=portal["connector_type"],
                    frequency="daily",
                    priority=1,
                    status="active",
                    health_status="Healthy",
                    last_crawl=datetime.now(timezone.utc) - timedelta(hours=2),
                    next_crawl=datetime.now(timezone.utc) + timedelta(hours=22)
                )
                db.add(src)
        db.commit()
        print("Seeded 25 initial procurement portals.")

        # 3. Seed Initial Keyword Groups
        keyword_seed = [
            {
                "name": "E-Learning & LMS Core",
                "positive": ["E-Learning", "Learning Management System", "LMS", "SCORM", "Storyline", "Rise 360", "Online Education", "Digital Learning"],
                "negative": ["Hardware", "Civil Works", "Construction"],
                "mandatory": ["Learning"],
                "priority_weight": 1.5,
                "color": "#8B5CF6"
            },
            {
                "name": "Content & Instructional Design",
                "positive": ["Instructional Design", "Content Development", "Digital Content", "Video Content", "Microlearning", "Four Quadrant Content"],
                "negative": ["Catering", "Security Guards"],
                "mandatory": ["Content"],
                "priority_weight": 1.2,
                "color": "#3B82F6"
            },
            {
                "name": "Skill & Vocational Education",
                "positive": ["NEP", "NSQF", "Higher Education", "School Education", "Skill Development", "K-12", "NCVET"],
                "negative": ["Janitorial"],
                "mandatory": ["Skill"],
                "priority_weight": 1.3,
                "color": "#10B981"
            }
        ]

        for kg in keyword_seed:
            existing = db.query(KeywordGroup).filter(KeywordGroup.name == kg["name"]).first()
            if not existing:
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
        print("Seeded initial keyword groups.")

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

        # 5. Seed Initial Organizations & Tenders for Live UI Demonstration
        org_gem = db.query(Organization).filter(Organization.name == "Ministry of Education, Govt of India").first()
        if not org_gem:
            org_gem = Organization(name="Ministry of Education, Govt of India", country="India", sector="Government", website="https://education.gov.in", previous_tenders_count=12)
            db.add(org_gem)
            db.commit()

        org_wb = db.query(Organization).filter(Organization.name == "World Bank Group").first()
        if not org_wb:
            org_wb = Organization(name="World Bank Group", country="International", sector="International", website="https://worldbank.org", previous_tenders_count=45)
            db.add(org_wb)
            db.commit()

        # Seed sample tender 1
        t1 = db.query(Tender).filter(Tender.tender_number == "GEM/2026/B/892341").first()
        if not t1:
            src_gem = db.query(Source).filter(Source.name.like("%GeM%")).first()
            t1 = Tender(
                tender_number="GEM/2026/B/892341",
                title="Development of Next-Gen AI-Powered LMS & Interactive SCORM Content for National Skill Portal",
                organization_id=org_gem.id,
                source_id=src_gem.id if src_gem else None,
                country="India",
                state="Delhi",
                sector="Education",
                budget=8500000.0,
                currency="INR",
                publication_date=datetime.now(timezone.utc) - timedelta(days=2),
                submission_deadline=datetime.now(timezone.utc) + timedelta(days=14),
                status="Active",
                access_status="Verified",
                official_link="https://gem.gov.in/show_bid/GEM-2026-B-892341",
                scope_of_work="Design, build, deploy, and maintain a high-concurrency Cloud LMS supporting 500k active students. Develop 200 hours of 4-Quadrant SCORM 1.2/2004 interactive modules in Articulate Storyline and Rise 360.",
                deliverables="1. Custom White-labeled LMS\n2. 200 SCORM Modules\n3. Native iOS & Android Apps\n4. AI Tutor Bot Integration",
                eligibility_criteria="Must have 5+ years experience in e-learning development with minimum 3 executed projects of value >= 50 Lakhs each in Govt/PSU sector.",
                technical_requirements="Moodle / Custom React+Python LMS, SCORM 1.2/2004, xAPI compliant, AWS Cloud setup, ISO 27001 certified.",
                financial_requirements="Minimum average annual turnover of ₹ 2 Crores in the last 3 financial years.",
                required_documents="1. Technical Proposal\n2. Financial Bid\n3. ISO Certificates\n4. Past Work Completion Certificates",
                ai_summary="High-value strategic opportunity matching 95% of core e-learning and LMS development capabilities. High win probability.",
                risk_analysis="Low operational risk. Tight timeline of 6 months for 200 hours of content.",
                bid_recommendation="Bid",
                winning_probability=92.0,
                estimated_team="1 ID Lead, 4 Storyline Developers, 2 Fullstack LMS Engineers, 1 QA",
                estimated_duration="6 Months",
                keyword_score=96.0,
                semantic_score=94.0,
                ai_score=95.0,
                priority_score=98.0,
                overall_match_score=95.5
            )
            db.add(t1)
            db.commit()

            # Add Attachment
            att = TenderAttachment(
                tender_id=t1.id,
                file_name="RFP_Specification_GEM_892341.pdf",
                file_type="PDF",
                file_path="./storage/rfp_892341.pdf",
                file_size_bytes=2450000,
                parsed_content="Complete RFP specifications for AI Powered LMS development and SCORM 1.2 content creation..."
            )
            db.add(att)
            
            # Add Version
            ver = TenderVersion(
                tender_id=t1.id,
                version_number=1,
                change_type="Original Release",
                notes="Initial RFP publication on GeM."
            )
            db.add(ver)
            db.commit()

        # Seed sample tender 2
        t2 = db.query(Tender).filter(Tender.tender_number == "WB-EDU-2026-104").first()
        if not t2:
            src_wb = db.query(Source).filter(Source.name.like("%World Bank%")).first()
            t2 = Tender(
                tender_number="WB-EDU-2026-104",
                title="Global Digital Learning Platform and Virtual Vocational Labs for Technical Universities",
                organization_id=org_wb.id,
                source_id=src_wb.id if src_wb else None,
                country="International",
                sector="International",
                budget=250000.0,
                currency="USD",
                publication_date=datetime.now(timezone.utc) - timedelta(days=5),
                submission_deadline=datetime.now(timezone.utc) + timedelta(days=20),
                status="Active",
                access_status="Verified",
                official_link="https://projects.worldbank.org/procurement/WB-EDU-2026-104",
                scope_of_work="Development of virtual 3D simulation labs for technical vocational training, multi-language localization (English, French, Spanish).",
                deliverables="10 Virtual Engineering Labs, LTI 1.3 LMS Integration, 3D WebGL interactive simulations.",
                eligibility_criteria="Global experience in vocational educational technology and multi-language deployment.",
                technical_requirements="WebGL, Unity 3D, HTML5, LTI 1.3 standard, WCAG 2.1 AAA Accessibility.",
                financial_requirements="Audited financial statements for last 3 years.",
                required_documents="Expression of Interest (EOI), Team CVs, Portfolio of 3D Learning Labs.",
                ai_summary="Excellent international consulting RFP for virtual labs and vocational digital content.",
                risk_analysis="Moderate complexity in multi-language translation and WebGL rendering speed.",
                bid_recommendation="Bid",
                winning_probability=88.0,
                estimated_team="1 Project Director, 2 3D Animators, 3 WebGL Developers, 2 Instructional Designers",
                estimated_duration="9 Months",
                keyword_score=92.0,
                semantic_score=90.0,
                ai_score=91.0,
                priority_score=94.0,
                overall_match_score=91.8
            )
            db.add(t2)
            db.commit()

            att2 = TenderAttachment(
                tender_id=t2.id,
                file_name="WorldBank_EOI_Virtual_Labs.pdf",
                file_type="PDF",
                file_path="./storage/wb_104.pdf",
                file_size_bytes=1800000,
                parsed_content="World Bank EOI document for global virtual vocational labs..."
            )
            db.add(att2)
            db.commit()

        print("Database seeding completed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
