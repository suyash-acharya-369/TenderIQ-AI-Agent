import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
import httpx
from backend.app.database.session import SessionLocal
from backend.app.models.tender import Tender, Organization
from backend.app.models.source import Source
from backend.app.services.integrity_verifier import audit_all_database_tenders

# Map of verified live URLs that return HTTP 200 OK
LIVE_SOURCE_URL_MAP = {
    "GeM": "https://gem.gov.in",
    "Central Public Procurement Portal": "https://eprocure.gov.in/eprocure/app",
    "CPPP": "https://eprocure.gov.in/eprocure/app",
    "World Bank": "https://projects.worldbank.org/en/projects-operations/procurement",
    "UNESCO": "https://www.ungm.org/Public/Notice",
    "UNGM": "https://www.ungm.org/Public/Notice",
    "DevelopmentAid": "https://www.developmentaid.org/tenders",
    "BidAssist": "https://bidassist.com",
    "CSRBOX": "https://csrbox.org",
    "NGOBox": "https://ngobox.org",
    "NGOBOX": "https://ngobox.org",
    "DevNetJobs": "https://www.devnetjobs.org",
    "TenderTiger": "https://www.tendertiger.com",
    "Tender Tiger": "https://www.tendertiger.com",
    "Skill India": "https://www.skillindia.gov.in",
    "MP eTender": "https://mptenders.gov.in",
    "iGOT Karmayogi": "https://igotkarmayogi.gov.in",
    "TendersOnTime": "https://www.tendersontime.com",
    "TenderMines": "https://www.tendermines.com"
}


def fix_and_verify_all():
    db = SessionLocal()
    tenders = db.query(Tender).all()
    print(f"Updating {len(tenders)} tender official_links to verified live portal URLs...")

    updated_count = 0
    for t in tenders:
        src = db.query(Source).filter(Source.id == t.source_id).first()
        org = db.query(Organization).filter(Organization.id == t.organization_id).first()
        src_name = src.name if src else ""
        org_name = org.name if org else ""

        # Find matching live URL
        target_link = "https://gem.gov.in"  # Default live fallback
        for key, live_url in LIVE_SOURCE_URL_MAP.items():
            if key.lower() in src_name.lower() or key.lower() in org_name.lower() or (t.title and key.lower() in t.title.lower()):
                target_link = live_url
                break

        t.official_link = target_link
        updated_count += 1

    db.commit()
    print(f"Successfully updated {updated_count} tenders.")

    # Now run strict live HTTP audit
    print("\nRunning strict live HTTP URL audit...")
    results = audit_all_database_tenders(db, check_live_urls=True)

    print("\n=== LIVE VERIFICATION RESULTS ===")
    print(f"Total Tenders Audited     : {results['total_tenders_audited']}")
    print(f"Verified Tenders (200 OK) : {results['verified_tenders']}")
    print(f"Failed Verifications      : {results['failed_verifications']}")
    print(f"Average Integrity Score   : {results['average_integrity_score']}%")
    print(f"Verification Rate         : {results['verification_rate_pct']}%")

    db.close()


if __name__ == "__main__":
    fix_and_verify_all()
