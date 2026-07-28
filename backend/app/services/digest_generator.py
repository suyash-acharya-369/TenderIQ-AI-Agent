import logging
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.app.models.tender import Tender
from backend.app.models.source import Source
from backend.app.models.user import User
from backend.app.models.notification import NotificationLog
from backend.app.services.notification_service import notification_service
from backend.app.ai.router import get_ai_provider

logger = logging.getLogger("TenderIQ.DigestGenerator")

def _render_stars(score: float) -> str:
    """Render trust score as HTML star badges."""
    stars = ""
    for i in range(1, 6):
        if i <= int(score):
            stars += "★"
        else:
            stars += "☆"
    return stars

def _render_tender_card(t, source_name: str, trust_score: float) -> str:
    """Render a single tender card with citations, evidence, portal badge, and PDF button."""
    # Evidence snippets
    evidence_html = ""
    kw_evidence = t.keyword_evidence or []
    if isinstance(kw_evidence, list):
        for ev in kw_evidence[:3]:
            kw = ev.get("keyword", "")
            sentence = ev.get("sentence", "")
            page = ev.get("page", "")
            section = ev.get("section", "")
            evidence_html += f'<div style="background:#f0fdf4;border-left:3px solid #22c55e;padding:6px 10px;margin:4px 0;font-size:12px;border-radius:4px;">'
            evidence_html += f'<b>{kw}</b> — "{sentence}" <span style="color:#6b7280;">[Page {page}, §{section}]</span></div>'

    # AI Citations
    citations_html = ""
    ai_citations = t.ai_citations or {}
    if isinstance(ai_citations, dict):
        citation_items = [f"<b>{k}</b>: {v}" for k, v in ai_citations.items()]
        if citation_items:
            citations_html = f'<div style="font-size:11px;color:#6b7280;margin-top:6px;">📌 Citations: {", ".join(citation_items)}</div>'

    # PDF button
    pdf_btn = ""
    if t.official_link:
        pdf_btn = f'<a href="{t.official_link}" style="display:inline-block;padding:6px 14px;background:#3b82f6;color:white;border-radius:6px;text-decoration:none;font-size:12px;margin-top:8px;">📄 View Document</a>'

    # Trust badge
    stars = _render_stars(trust_score)

    match_color = "#059669" if t.overall_match_score >= 80 else "#eab308" if t.overall_match_score >= 60 else "#ef4444"

    return f"""
    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin:12px 0;background:white;">
        <div style="display:flex;justify-content:space-between;align-items:start;">
            <div style="flex:1;">
                <h3 style="margin:0 0 6px 0;font-size:15px;color:#1e293b;">{t.title[:120]}</h3>
                <div style="font-size:12px;color:#64748b;">
                    {source_name} <span style="color:#eab308;">{stars}</span> &nbsp;|&nbsp; 
                    {t.sector or 'General'} &nbsp;|&nbsp; {t.country or 'India'}
                </div>
            </div>
            <div style="text-align:right;min-width:80px;">
                <div style="font-size:24px;font-weight:bold;color:{match_color};">{t.overall_match_score:.0f}%</div>
                <div style="font-size:10px;color:#94a3b8;">Match Score</div>
            </div>
        </div>
        <div style="margin-top:10px;font-size:13px;color:#475569;line-height:1.5;">
            {(t.ai_summary or '')[:300]}
        </div>
        {evidence_html}
        {citations_html}
        <div style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;">
            <div style="font-size:11px;color:#94a3b8;">
                💰 {t.currency or 'INR'} {t.budget:,.0f if t.budget else 'N/A'} &nbsp;|&nbsp;
                📅 Deadline: {t.submission_deadline.strftime('%b %d, %Y') if t.submission_deadline else 'TBD'} &nbsp;|&nbsp;
                🏷️ {t.bid_recommendation or 'Consider'}
            </div>
            {pdf_btn}
        </div>
    </div>
    """

def generate_and_dispatch_daily_digest(db: Session):
    """Block 7: Enhanced Daily Digest with evidence, citations, badges, PDF links, and QA guard."""
    logger.info("Starting Enhanced Daily Digest generation...")
    
    # 1. Fetch users opted into digest
    users_with_prefs = db.query(User).filter(User.notification_preferences.is_not(None), User.is_active == True).all()
    digest_recipients = []
    for u in users_with_prefs:
        prefs = u.notification_preferences or {}
        if prefs.get("daily_digest_enabled", False):
            digest_recipients.append(u.email)
            
    if not digest_recipients:
        logger.info("No users opted in for Daily Digest. Skipping.")
        return
        
    # 2. Fetch last 24h tenders
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    tenders = db.query(Tender).filter(Tender.created_at >= yesterday).all()
    
    if not tenders:
        logger.info("No new tenders in the last 24h. Skipping digest.")
        return

    # 3. QA Guard — only include tenders with verification_status VERIFIED and integrity_score >= 50
    verified_tenders = [t for t in tenders if (t.verification_status or "") == "VERIFIED" and (t.integrity_score or 0) >= 50]
    rejected_count = len(tenders) - len(verified_tenders)
    
    if not verified_tenders:
        logger.info(f"All {len(tenders)} tenders failed QA guard. Skipping digest.")
        return
    
    # 4. Sort by match score
    verified_tenders.sort(key=lambda t: t.overall_match_score or 0, reverse=True)
    high_match = [t for t in verified_tenders if (t.overall_match_score or 0) >= 80]
    
    # 5. Build tender cards with source trust badges
    tender_cards_html = ""
    for t in verified_tenders[:15]:
        source = db.query(Source).filter(Source.id == t.source_id).first()
        source_name = source.name if source else "Unknown Portal"
        trust_score = source.trust_score if source else 3.0
        tender_cards_html += _render_tender_card(t, source_name, trust_score)
    
    # 6. Build summary statistics
    total_new = len(verified_tenders)
    avg_score = sum(t.overall_match_score or 0 for t in verified_tenders) / max(total_new, 1)
    
    subject = f"📊 TenderIQ Daily Intelligence — {datetime.now().strftime('%b %d, %Y')} | {total_new} Verified Tenders"
    
    final_html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 680px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: #f8fafc;">
        <div style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 28px; color: white; text-align: center;">
            <h1 style="margin:0;font-size:22px;">🔍 TenderIQ Daily Intelligence</h1>
            <p style="margin:8px 0 0;font-size:13px;opacity:0.85;">{datetime.now().strftime('%A, %B %d, %Y')} • Enterprise Procurement Dashboard</p>
        </div>
        
        <div style="display:flex;justify-content:space-around;padding:16px 20px;background:white;border-bottom:1px solid #e2e8f0;">
            <div style="text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#1e1b4b;">{total_new}</div>
                <div style="font-size:11px;color:#64748b;">Verified Tenders</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#059669;">{len(high_match)}</div>
                <div style="font-size:11px;color:#64748b;">High Match (80%+)</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#3b82f6;">{avg_score:.0f}%</div>
                <div style="font-size:11px;color:#64748b;">Avg Match Score</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:28px;font-weight:bold;color:#ef4444;">{rejected_count}</div>
                <div style="font-size:11px;color:#64748b;">QA Rejected</div>
            </div>
        </div>
        
        <div style="padding: 20px;">
            <h2 style="font-size:16px;color:#1e293b;margin:0 0 12px;">📋 Top Opportunities</h2>
            {tender_cards_html}
        </div>
        
        <div style="background: #f1f5f9; padding: 16px; text-align: center; font-size: 11px; color: #64748b; border-top:1px solid #e2e8f0;">
            <p style="margin:0;">This digest contains only <b>verified</b> tenders that passed QA integrity checks.</p>
            <p style="margin:4px 0 0;">You received this because you are subscribed to the Daily Digest. <a href="#" style="color:#3b82f6;">Manage Preferences</a></p>
        </div>
    </div>
    """
    
    # 7. Dispatch to all recipients
    dispatched = 0
    for email in digest_recipients:
        success = notification_service.dispatch_email(email, subject, final_html)
        db.add(NotificationLog(
            channel="Email",
            recipient=email,
            subject=subject,
            content=final_html,
            status="sent" if success else "failed"
        ))
        if success:
            dispatched += 1
            
    db.commit()
    logger.info(f"Enhanced Daily Digest dispatched to {dispatched}/{len(digest_recipients)} users. {rejected_count} tenders QA-rejected.")
