import json
import logging
from typing import List, Dict, Any, Set
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.notification import NotificationRule, NotificationLog, InAppNotification
from backend.app.models.tender import Tender, TenderAttachment
from backend.app.models.keyword import KeywordGroup
from backend.app.models.user import User
from backend.app.services.notification_service import notification_service
from backend.app.notifications.whatsapp import send_whatsapp_notification
from backend.app.services.rules_evaluator import evaluate_condition
from backend.app.notifications.templates import tender_alert_template

logger = logging.getLogger("TenderIQ.NotificationsEngine")


def evaluate_and_dispatch_notifications(tender: Tender, db: Session) -> int:
    """Phase 2, 4, 5, 6, 7, 9 & 12: Autonomous notification engine with duplicate guard and rule evaluation."""
    dispatched_count = 0
    recipients_to_email: Set[str] = set()
    recipients_to_wa: Set[str] = set()
    user_ids_to_notify: Set[int] = set()

    # Data Integrity Verification Policy: Prioritize accuracy over quantity
    if tender.verification_status and tender.verification_status != "VERIFIED":
        logger.warning(f"Data Integrity Policy: Skipping notification for unverified tender {tender.tender_number} (status={tender.verification_status})")
        return 0

    # Phase 20: Mark lifecycle stage
    tender.lifecycle_stage = "Notified"
    db.commit()

    # 1. Rule Engine Evaluation (Phase 5)
    rules = db.query(NotificationRule).filter(NotificationRule.is_active == 1).all()
    for rule in rules:
        min_score = rule.min_score_threshold or 80.0
        if tender.overall_match_score < min_score:
            continue

        if rule.conditions:
            if not evaluate_condition(tender, rule.conditions):
                continue

        channels = rule.channels or ["Email"]
        for rec in (rule.recipients or []):
            if "Email" in channels or "email" in channels:
                recipients_to_email.add(rec)
            if "WhatsApp" in channels or "whatsapp" in channels:
                recipients_to_wa.add(rec)

    # 2. Keyword-based Multi-Recipient Routing (Phase 6)
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

                    if kg.routed_roles:
                        users = db.query(User).filter(User.role.in_(kg.routed_roles), User.is_active == True).all()
                        for u in users:
                            recipients_to_email.add(u.email)
                            user_ids_to_notify.add(u.id)
        except Exception as e:
            logger.error(f"Failed to route by keywords: {e}")

    # 3. User Preferences (Phase 9)
    users_with_prefs = db.query(User).filter(User.notification_preferences.is_not(None), User.is_active == True).all()
    for u in users_with_prefs:
        prefs = u.notification_preferences or {}
        if prefs.get("instant_alerts_enabled", True):
            subbed = prefs.get("subscribed_keywords", [])
            if not subbed or any(k in subbed for k in keywords_matched):
                recipients_to_email.add(u.email)
                user_ids_to_notify.add(u.id)

    # Prepare Template Payload
    tmpl = tender_alert_template(
        tender_title=tender.title,
        source=tender.country or "Global Portal",
        match_score=tender.overall_match_score or 90.0,
    )
    subject = tmpl["subject"]
    content = tmpl["html"]

    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Dispatch Emails with Phase 4 Duplicate Prevention Guard
    for email in recipients_to_email:
        # Check duplicate
        existing = db.query(NotificationLog).filter(
            NotificationLog.recipient == email,
            NotificationLog.subject == subject,
            NotificationLog.status == "sent"
        ).first()

        if existing:
            logger.info(f"Phase 4: Skipping duplicate notification to {email} for tender {tender.tender_number}")
            skipped = NotificationLog(
                channel="Email",
                recipient=email,
                subject=subject,
                content="[Skipped Duplicate Guard]",
                status="skipped_duplicate",
                sent_at=datetime.now(timezone.utc)
            )
            db.add(skipped)
            continue

        # Phase 7: Attachments Handling
        attachment = db.query(TenderAttachment).filter(TenderAttachment.tender_id == tender.id).first()

        result = notification_service.dispatch_email(email, subject, content)

        log = NotificationLog(
            channel="Email",
            recipient=email,
            subject=subject,
            content=content,
            status="sent" if result.success else "failed",
            message_id=result.message_id,
            provider=result.provider,
            http_status=result.http_status,
            provider_response=result.provider_response,
            retry_count=result.retry_count,
            error_message=result.error
        )
        db.add(log)
        dispatched_count += 1

    # Dispatch WhatsApp
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
