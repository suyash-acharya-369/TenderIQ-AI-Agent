"""
Production-grade HTML email templates for TenderIQ AI notification system.
"""
from datetime import datetime, timezone


BRAND_COLOR = "#4F46E5"
BRAND_NAME = "TenderIQ AI"
FOOTER = f"""
<div style="margin-top:32px; padding-top:24px; border-top:1px solid #E5E7EB; text-align:center; color:#9CA3AF; font-size:12px;">
    <p>{BRAND_NAME} &middot; Enterprise Tender Intelligence</p>
    <p style="margin-top:4px;">This is an automated message. Please do not reply directly.</p>
</div>
"""

TEST_BANNER = """
<div style="background:#FEF3C7; border:1px solid #F59E0B; border-radius:8px; padding:12px 16px; margin-bottom:24px; text-align:center;">
    <strong style="color:#92400E;">⚠️ TEST EMAIL — Development Environment — Do Not Take Action</strong>
</div>
"""


def _wrap(body_html: str, is_test: bool = False) -> str:
    """Wrap content in the standard TenderIQ email layout."""
    test_section = TEST_BANNER if is_test else ""
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background-color:#F3F4F6; font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
<div style="max-width:600px; margin:32px auto; background:#FFFFFF; border-radius:12px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">
    <div style="background:{BRAND_COLOR}; padding:24px 32px;">
        <h1 style="margin:0; color:#FFFFFF; font-size:22px; font-weight:700;">{BRAND_NAME}</h1>
        <p style="margin:4px 0 0; color:#C7D2FE; font-size:13px;">Enterprise Tender Intelligence Platform</p>
    </div>
    <div style="padding:32px;">
        {test_section}
        {body_html}
        {FOOTER}
    </div>
</div>
</body>
</html>
"""


def test_email_template(provider_name: str, environment: str = "Development") -> dict:
    """Basic connectivity test email."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    body = f"""
    <h2 style="color:#111827; margin-bottom:16px;">Email System Verification</h2>
    <p style="color:#374151; line-height:1.6;">
        Hello,<br><br>
        This is a test email from the TenderIQ AI Notification System.<br>
        If you have received this email, the email delivery pipeline is functioning correctly.
    </p>
    <table style="width:100%; border-collapse:collapse; margin-top:24px; font-size:14px;">
        <tr style="border-bottom:1px solid #E5E7EB;">
            <td style="padding:10px 0; color:#6B7280; font-weight:500;">Timestamp</td>
            <td style="padding:10px 0; color:#111827;">{now}</td>
        </tr>
        <tr style="border-bottom:1px solid #E5E7EB;">
            <td style="padding:10px 0; color:#6B7280; font-weight:500;">Provider</td>
            <td style="padding:10px 0; color:#111827;">{provider_name}</td>
        </tr>
        <tr>
            <td style="padding:10px 0; color:#6B7280; font-weight:500;">Environment</td>
            <td style="padding:10px 0; color:#111827;">{environment}</td>
        </tr>
    </table>
    """
    return {
        "subject": "TenderIQ AI - Email System Verification",
        "html": _wrap(body, is_test=True),
    }


def welcome_template(user_name: str = "User") -> dict:
    body = f"""
    <h2 style="color:#111827;">Welcome to {BRAND_NAME}!</h2>
    <p style="color:#374151; line-height:1.6;">
        Hello {user_name},<br><br>
        Your account has been successfully created on the TenderIQ AI platform.
        You can now access the dashboard, manage procurement sources, configure keyword groups, and receive AI-powered tender intelligence.
    </p>
    <div style="text-align:center; margin:32px 0;">
        <a href="#" style="background:{BRAND_COLOR}; color:#FFFFFF; padding:12px 32px; border-radius:8px; text-decoration:none; font-weight:600; display:inline-block;">Go to Dashboard</a>
    </div>
    """
    return {
        "subject": f"Welcome to {BRAND_NAME}",
        "html": _wrap(body, is_test=True),
    }


def tender_alert_template(tender_title: str = "E-Learning Platform Development", source: str = "GeM Portal", match_score: float = 94.5) -> dict:
    body = f"""
    <h2 style="color:#111827;">🔔 New Tender Alert</h2>
    <p style="color:#374151; line-height:1.6;">A new high-priority tender matching your keyword groups has been discovered.</p>
    <div style="background:#F0FDF4; border-left:4px solid #22C55E; padding:16px; border-radius:0 8px 8px 0; margin:20px 0;">
        <h3 style="margin:0 0 8px; color:#166534;">{tender_title}</h3>
        <p style="margin:0; color:#15803D; font-size:14px;">Source: {source} &middot; Match Score: {match_score}%</p>
    </div>
    <div style="text-align:center; margin:24px 0;">
        <a href="#" style="background:{BRAND_COLOR}; color:#FFFFFF; padding:12px 32px; border-radius:8px; text-decoration:none; font-weight:600; display:inline-block;">View Tender Details</a>
    </div>
    """
    return {
        "subject": f"🔔 New Tender: {tender_title}",
        "html": _wrap(body, is_test=True),
    }


def ai_summary_template() -> dict:
    body = f"""
    <h2 style="color:#111827;">🤖 AI Analysis Complete</h2>
    <p style="color:#374151; line-height:1.6;">The AI engine has completed analysis of recently discovered tenders.</p>
    <table style="width:100%; border-collapse:collapse; margin-top:16px; font-size:14px;">
        <tr style="border-bottom:1px solid #E5E7EB;">
            <td style="padding:10px 0; color:#6B7280;">Tenders Analyzed</td>
            <td style="padding:10px 0; color:#111827; font-weight:600;">12</td>
        </tr>
        <tr style="border-bottom:1px solid #E5E7EB;">
            <td style="padding:10px 0; color:#6B7280;">High Match</td>
            <td style="padding:10px 0; color:#22C55E; font-weight:600;">4</td>
        </tr>
        <tr>
            <td style="padding:10px 0; color:#6B7280;">Recommendations</td>
            <td style="padding:10px 0; color:#111827; font-weight:600;">3 tenders recommended for bid</td>
        </tr>
    </table>
    """
    return {
        "subject": "🤖 AI Analysis Summary — TenderIQ AI",
        "html": _wrap(body, is_test=True),
    }


def crawl_completed_template(source_name: str = "GeM Portal", tenders_found: int = 8) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    body = f"""
    <h2 style="color:#111827;">✅ Crawl Completed</h2>
    <p style="color:#374151; line-height:1.6;">A scheduled crawl has finished processing.</p>
    <table style="width:100%; border-collapse:collapse; margin-top:16px; font-size:14px;">
        <tr style="border-bottom:1px solid #E5E7EB;">
            <td style="padding:10px 0; color:#6B7280;">Source</td>
            <td style="padding:10px 0; color:#111827;">{source_name}</td>
        </tr>
        <tr style="border-bottom:1px solid #E5E7EB;">
            <td style="padding:10px 0; color:#6B7280;">Tenders Found</td>
            <td style="padding:10px 0; color:#111827; font-weight:600;">{tenders_found}</td>
        </tr>
        <tr>
            <td style="padding:10px 0; color:#6B7280;">Completed At</td>
            <td style="padding:10px 0; color:#111827;">{now}</td>
        </tr>
    </table>
    """
    return {
        "subject": f"✅ Crawl Completed: {source_name} — TenderIQ AI",
        "html": _wrap(body, is_test=True),
    }


def daily_digest_template() -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = f"""
    <h2 style="color:#111827;">📊 Daily Digest — {now}</h2>
    <p style="color:#374151; line-height:1.6;">Here is your daily summary of procurement intelligence activity.</p>
    <div style="display:grid; gap:12px; margin:20px 0;">
        <div style="background:#EFF6FF; padding:16px; border-radius:8px;">
            <p style="margin:0; color:#1E40AF; font-size:28px; font-weight:700;">24</p>
            <p style="margin:4px 0 0; color:#3B82F6; font-size:13px;">New Tenders Discovered</p>
        </div>
        <div style="background:#F0FDF4; padding:16px; border-radius:8px;">
            <p style="margin:0; color:#166534; font-size:28px; font-weight:700;">6</p>
            <p style="margin:4px 0 0; color:#22C55E; font-size:13px;">High Match Score (&gt;90%)</p>
        </div>
        <div style="background:#FEF3C7; padding:16px; border-radius:8px;">
            <p style="margin:0; color:#92400E; font-size:28px; font-weight:700;">3</p>
            <p style="margin:4px 0 0; color:#F59E0B; font-size:13px;">Closing Within 7 Days</p>
        </div>
    </div>
    """
    return {
        "subject": f"📊 Daily Digest — {now} — TenderIQ AI",
        "html": _wrap(body, is_test=True),
    }


def system_alert_template(alert_message: str = "System health check completed successfully.") -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    body = f"""
    <h2 style="color:#111827;">⚙️ System Alert</h2>
    <div style="background:#FEF2F2; border-left:4px solid #EF4444; padding:16px; border-radius:0 8px 8px 0; margin:16px 0;">
        <p style="margin:0; color:#991B1B; font-weight:500;">{alert_message}</p>
    </div>
    <p style="color:#6B7280; font-size:13px; margin-top:12px;">Timestamp: {now}</p>
    """
    return {
        "subject": "⚙️ System Alert — TenderIQ AI",
        "html": _wrap(body, is_test=True),
    }
