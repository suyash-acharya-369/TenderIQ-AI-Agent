import logging
from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from backend.app.models.notification import NotificationRule, NotificationLog, InAppNotification
from backend.app.models.tender import Tender
from backend.app.models.keyword import KeywordGroup
from backend.app.models.user import User
from backend.app.services.notification_service import notification_service
from backend.app.notifications.whatsapp import send_whatsapp_notification
from backend.app.services.rules_evaluator import evaluate_condition
import json

logger = logging.getLogger("TenderIQ.NotificationsEngine")

def evaluate_and_dispatch_notifications(tender: Tender, db: Session) -> int:
    """Evaluate a newly indexed or high-priority tender against active NotificationRules and User preferences, and dispatch alerts."""
    dispatched_count = 0
    recipients_to_email: Set[str] = set()
    recipients_to_wa: Set[str] = set()
    user_ids_to_notify: Set[int] = set()
    
    # 1. Rule Engine Evaluation
    rules = db.query(NotificationRule).filter(NotificationRule.is_active == 1).all()
    for rule in rules:
        # Check standard threshold
        min_score = rule.min_score_threshold or 90.0
        if tender.overall_match_score < min_score:
            continue
            
        # Check dynamic JSON conditions
        if rule.conditions:
            if not evaluate_condition(tender, rule.conditions):
                continue

        channels = rule.channels or ["Email"]
        for rec in (rule.recipients or []):
            if "Email" in channels or "email" in channels:
                recipients_to_email.add(rec)
            if "WhatsApp" in channels or "whatsapp" in channels:
                recipients_to_wa.add(rec)
                
    # 2. Keyword-based Routing
    keywords_matched = tender.raw_metadata.get("keywords_matched", []) if tender.raw_metadata else []
    if keywords_matched:
        try:
            matched_list = json.loads(keywords_matched) if isinstance(keywords_matched, str) else keywords_matched
            for k_name in matched_list:
                kg = db.query(KeywordGroup).filter(KeywordGroup.name == k_name, KeywordGroup.status == "active").first()
                if kg:
                    if kg.routed_recipients:
                        for rec in kg.routed_recipients:
                            recipients_to_email.add(rec)
                    
                    # Resolve routed roles/teams to users
                    # Simulated for now: If a user's role is in routed_roles, add their email
                    if kg.routed_roles:
                        users = db.query(User).filter(User.role.in_(kg.routed_roles), User.is_active == True).all()
                        for u in users:
                            recipients_to_email.add(u.email)
                            user_ids_to_notify.add(u.id)
                            
        except Exception as e:
            logger.error(f"Failed to route by keywords: {e}")
            
    # 3. User Preferences (Opt-ins)
    users_with_prefs = db.query(User).filter(User.notification_preferences.is_not(None), User.is_active == True).all()
    for u in users_with_prefs:
        prefs = u.notification_preferences or {}
        if prefs.get("instant_alerts_enabled"):
            # Check if user subscribed to specific keywords
            subbed = prefs.get("subscribed_keywords", [])
            if not subbed or any(k in subbed for k in keywords_matched):
                recipients_to_email.add(u.email)
                user_ids_to_notify.add(u.id)

    # Dispatch Emails
    subject = f"🚨 High Priority Tender Alert: [{tender.tender_number}] {tender.title[:60]}"
    content = f"""
        <h2>TenderIQ AI High-Priority Alert</h2>
        <p><strong>Tender Number:</strong> {tender.tender_number}</p>
        <p><strong>Title:</strong> {tender.title}</p>
        <p><strong>Match Score:</strong> <span style="color:#8a2be2; font-weight:bold;">{tender.overall_match_score}%</span></p>
        <p><strong>Bid Recommendation:</strong> {tender.bid_recommendation} ({tender.winning_probability}% Win Prob)</p>
        <p><strong>Country / Sector:</strong> {tender.country} | {tender.sector}</p>
        <p><strong>Scope:</strong> {tender.scope_of_work}</p>
        <p><a href="http://127.0.0.1:8000/opportunities" style="padding:10px 15px; background:#4f46e5; color:#fff; text-decoration:none; border-radius:5px;">View Tender Details</a></p>
    """
    
    for email in recipients_to_email:
        # In a real async setup, we'd use BackgroundTasks or Celery here
        success = notification_service.dispatch_email(email, subject, content)
        log = NotificationLog(
            channel="Email",
            recipient=email,
            subject=subject,
            content=content,
            status="sent" if success else "failed"
        )
        db.add(log)
        dispatched_count += 1
        
    for phone in recipients_to_wa:
        wa_msg = f"🚨 *TenderIQ Alert*\n*{tender.tender_number}*\n{tender.title}\nMatch: {tender.overall_match_score}%\nRec: {tender.bid_recommendation}"
        success = send_whatsapp_notification(phone, wa_msg)
        log = NotificationLog(
            channel="WhatsApp",
            recipient=phone,
            subject=f"WA Alert: {tender.tender_number}",
            content=wa_msg,
            status="sent" if success else "failed"
        )
        db.add(log)
        dispatched_count += 1
        
    # Generate In-App Notifications
    for uid in user_ids_to_notify:
        in_app = InAppNotification(
            user_id=uid,
            title=f"New High Match Tender: {tender.tender_number}",
            content=f"Found new opportunity matching your keywords. Score: {tender.overall_match_score}%",
            action_url="/opportunities",
            event_type="tender.matched",
            tender_id=tender.id,
            source_id=tender.source_id,
            priority="high",
            lifecycle_status="Created"
        )
        db.add(in_app)

    db.commit()
    logger.info(f"Dispatched {dispatched_count} notifications for tender {tender.tender_number}")
    return dispatched_count
