from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.notification import NotificationRule, NotificationLog
from backend.app.models.user import User
from backend.app.notifications.email import send_email_notification
from backend.app.notifications.whatsapp import send_whatsapp_notification
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationRuleCreate(BaseModel):
    name: str
    min_score_threshold: Optional[float] = 90.0
    channels: List[str]  # ["Email", "WhatsApp"]
    event_types: List[str]  # ["HighPriority", "Corrigendum"]
    recipients: List[str]

class NotificationRuleUpdate(BaseModel):
    name: Optional[str] = None
    min_score_threshold: Optional[float] = None
    channels: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    recipients: Optional[List[str]] = None
    is_active: Optional[int] = None

class TestDispatchPayload(BaseModel):
    channel: str  # Email or WhatsApp
    recipient: str
    message: str

@router.get("/rules")
def list_notification_rules(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(NotificationRule).all()

@router.post("/rules")
def create_notification_rule(
    payload: NotificationRuleCreate,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    rule = NotificationRule(
        name=payload.name,
        min_score_threshold=payload.min_score_threshold,
        channels=payload.channels,
        event_types=payload.event_types,
        recipients=payload.recipients,
        is_active=1
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.put("/rules/{rule_id}")
def update_notification_rule(
    rule_id: int,
    payload: NotificationRuleUpdate,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Notification Rule not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/rules/{rule_id}")
def delete_notification_rule(
    rule_id: int,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    rule = db.query(NotificationRule).filter(NotificationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Notification Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "success", "deleted_id": rule_id}

@router.get("/logs")
def list_notification_logs(
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(limit).all()

@router.post("/test-dispatch")
def test_dispatch_notification(
    payload: TestDispatchPayload,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    from backend.app.services.notification_service import notification_service
    success = False
    if payload.channel.lower() == "email":
        success = notification_service.dispatch_email(payload.recipient, "TenderIQ AI Test Alert", f"<p>{payload.message}</p>")
    elif payload.channel.lower() == "whatsapp":
        success = send_whatsapp_notification(payload.recipient, payload.message)

    log = NotificationLog(
        channel=payload.channel,
        recipient=payload.recipient,
        subject="TenderIQ Test Dispatch",
        content=payload.message,
        status="sent" if success else "failed"
    )
    db.add(log)
    db.commit()

    return {"status": "success" if success else "failed", "channel": payload.channel, "recipient": payload.recipient}


from backend.app.models.notification import InAppNotification
from datetime import datetime, timezone
from fastapi import Request, WebSocket, WebSocketDisconnect
from typing import Optional
from backend.app.api.websockets import notification_manager

class NotificationPatch(BaseModel):
    is_read: Optional[int] = None
    is_archived: Optional[int] = None

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # In a real app, you would authenticate the connection with a token here.
    # For now, we connect and wait for the client to send an auth payload.
    await notification_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # If the client sends {"token": "...", "user_id": 1}
            # we can authenticate them.
            try:
                payload = json.loads(data)
                if "user_id" in payload:
                    notification_manager.authenticate_connection(websocket, int(payload["user_id"]))
            except:
                pass
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)

@router.get("/in-app")
def get_in_app_notifications(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    status: Optional[str] = Query(None), # "unread", "archived"
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    query = db.query(InAppNotification).filter(
        InAppNotification.user_id == current_user.id,
        InAppNotification.is_deleted == 0
    )
    
    if status == "unread":
        query = query.filter(InAppNotification.is_read == 0, InAppNotification.is_archived == 0)
    elif status == "archived":
        query = query.filter(InAppNotification.is_archived == 1)
    else:
        query = query.filter(InAppNotification.is_archived == 0)
        
    return query.order_by(InAppNotification.created_at.desc()).offset(offset).limit(limit).all()
@router.patch("/in-app/{notif_id}")
def patch_in_app_notification(
    notif_id: int, 
    payload: NotificationPatch, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    notif = db.query(InAppNotification).filter(InAppNotification.id == notif_id, InAppNotification.user_id == current_user.id).first()
    if notif:
        if payload.is_read is not None:
            notif.is_read = payload.is_read
            if payload.is_read == 1:
                notif.lifecycle_status = "Read"
        if payload.is_archived is not None:
            notif.is_archived = payload.is_archived
            notif.archived_at = datetime.now(timezone.utc) if payload.is_archived else None
            if payload.is_archived == 1:
                notif.lifecycle_status = "Archived"
        db.commit()
    return {"status": "success"}

@router.post("/in-app/mark-all-read")
def mark_all_in_app_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(InAppNotification).filter(
        InAppNotification.user_id == current_user.id,
        InAppNotification.is_read == 0
    ).update({
        "is_read": 1, 
        "lifecycle_status": "Read"
    }, synchronize_session=False)
    db.commit()
    return {"status": "success"}

@router.delete("/in-app/{notif_id}")
def delete_in_app_notification(notif_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(InAppNotification).filter(InAppNotification.id == notif_id, InAppNotification.user_id == current_user.id).first()
    if notif:
        notif.is_deleted = 1
        notif.deleted_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "success"}

@router.post("/webhook")
async def resend_webhook(request: Request, db: Session = Depends(get_db)):
    # Standard implementation for parsing resend webhooks
    data = await request.json()
    event_type = data.get("type")
    
    if data.get("data") and data["data"].get("email_id"):
        # In a real impl, we'd lookup by email_id, here we mock it based on email address
        # as we are just saving timestamps
        email_to = data["data"].get("to", [""])[0]
        log = db.query(NotificationLog).filter(NotificationLog.recipient == email_to).order_by(NotificationLog.sent_at.desc()).first()
        
        if log:
            if event_type == "email.opened":
                log.opened_at = datetime.now(timezone.utc)
            elif event_type == "email.clicked":
                log.clicked_at = datetime.now(timezone.utc)
            db.commit()
    return {"status": "processed"}

@router.get("/logs")
def get_notification_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(100).all()
