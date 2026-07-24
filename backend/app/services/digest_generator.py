import logging
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.app.models.tender import Tender
from backend.app.models.user import User
from backend.app.models.notification import NotificationLog
from backend.app.services.notification_service import notification_service
from backend.app.ai.router import get_ai_provider

logger = logging.getLogger("TenderIQ.DigestGenerator")

def generate_and_dispatch_daily_digest(db: Session):
    """Aggregates tenders from the last 24h, uses AI to create a digest, and emails opted-in users."""
    logger.info("Starting Daily Digest generation...")
    
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
        
    # 3. Aggregate data for AI
    high_match = [t for t in tenders if t.overall_match_score >= 80]
    total_new = len(tenders)
    
    prompt_context = f"We found {total_new} new procurement opportunities in the last 24 hours. Here are the top matches:\n"
    for t in high_match[:10]: # Limit to top 10 for context window
        prompt_context += f"- Title: {t.title}\n  Score: {t.overall_match_score}\n  Sector: {t.sector}\n  Deadline: {t.submission_deadline}\n  Summary: {t.ai_summary}\n\n"
        
    system_prompt = "You are an expert procurement analyst. Write a concise, professional executive summary (Daily Digest) of the following new tenders. Highlight key trends, top recommended opportunities, and actionable insights. Format your response in clean HTML without markdown blocks."
    
    # 4. Generate AI Summary
    ai = get_ai_provider()
    try:
        digest_html_content = ai.analyze(prompt_context, system_prompt)
    except Exception as e:
        logger.error(f"AI Digest Generation failed: {e}")
        return
        
    # 5. Build Final Template and Dispatch
    subject = f"📊 TenderIQ Daily Digest - {datetime.now().strftime('%b %d, %Y')}"
    
    # In a real app, we would load from backend/app/templates/email/daily_digest.html
    # Here we wrap the AI output in standard branding.
    final_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
        <div style="background: #1e1b4b; padding: 20px; color: white; text-align: center;">
            <h2>TenderIQ Daily Intelligence</h2>
        </div>
        <div style="padding: 20px; color: #333; line-height: 1.6;">
            {digest_html_content}
        </div>
        <div style="background: #f8fafc; padding: 15px; text-align: center; font-size: 12px; color: #64748b;">
            <p>You received this because you are subscribed to the Daily Digest.</p>
        </div>
    </div>
    """
    
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
    logger.info(f"Dispatched Daily Digest to {dispatched} users.")
