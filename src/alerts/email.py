from datetime import date
from typing import Optional

import resend
from loguru import logger

from src.config import settings
from src.db.models import RuleChange, User, PolicyDocument

resend.api_key = settings.resend_api_key

IMPACT_COLOR = {"high": "#DC2626", "medium": "#D97706", "low": "#16A34A"}
IMPACT_BADGE = {"high": "HIGH IMPACT", "medium": "MEDIUM IMPACT", "low": "LOW IMPACT"}


def _change_block(change: RuleChange, index: int, total: int) -> str:
    color = IMPACT_COLOR.get(change.impact_level, "#6B7280")
    badge = IMPACT_BADGE.get(change.impact_level, "INFO")
    action_html = ""
    if change.action_required and change.action_description:
        action_html = f"""
        <div style="background:#FEF3C7;border-left:4px solid #F59E0B;padding:12px 16px;margin-top:16px;border-radius:0 6px 6px 0;">
          <strong style="color:#92400E;">Action Required:</strong>
          <p style="margin:6px 0 0;color:#78350F;">{change.action_description}</p>
        </div>"""

    visa_tags = "".join(
        f'<span style="display:inline-block;background:#EFF6FF;color:#1D4ED8;border-radius:4px;padding:2px 8px;font-size:12px;margin:2px;">{v}</span>'
        for v in (change.visa_categories_affected or [])
    )

    return f"""
    <div style="border:1px solid #E5E7EB;border-radius:8px;padding:24px;margin-bottom:24px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
        <span style="font-size:12px;color:#6B7280;">Change {index} of {total}</span>
        <span style="background:{color};color:white;font-size:11px;font-weight:700;padding:3px 10px;border-radius:4px;">{badge}</span>
      </div>
      <h3 style="margin:0 0 4px;font-size:18px;color:#111827;">{change.topic}</h3>
      <p style="margin:0 0 12px;font-size:13px;color:#6B7280;">Section: {change.section or 'N/A'}</p>
      <div style="margin-bottom:12px;">{visa_tags}</div>

      <p style="margin:0 0 16px;font-size:15px;color:#374151;line-height:1.6;">{change.plain_english_summary}</p>

      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr>
          <td style="width:50%;padding:12px;background:#FEF2F2;border-radius:6px 0 0 6px;vertical-align:top;">
            <strong style="color:#991B1B;display:block;margin-bottom:6px;">BEFORE</strong>
            <span style="color:#374151;line-height:1.5;">{change.old_rule}</span>
          </td>
          <td style="width:4px;background:white;"></td>
          <td style="width:50%;padding:12px;background:#F0FDF4;border-radius:0 6px 6px 0;vertical-align:top;">
            <strong style="color:#166534;display:block;margin-bottom:6px;">AFTER</strong>
            <span style="color:#374151;line-height:1.5;">{change.new_rule}</span>
          </td>
        </tr>
      </table>
      {action_html}
    </div>"""


def build_email_html(user: User, changes: list[RuleChange], documents: list[PolicyDocument]) -> str:
    today = date.today().strftime("%B %d, %Y")
    change_blocks = "".join(_change_block(c, i + 1, len(changes)) for i, c in enumerate(changes))
    high_count = sum(1 for c in changes if c.impact_level == "high")
    subject_prefix = "[HIGH IMPACT] " if high_count > 0 else ""

    doc_links = "".join(
        f'<li><a href="{d.source_url}" style="color:#2563EB;">{d.title}</a> — Published {d.published_at}</li>'
        for d in documents
    )

    visa_label = ", ".join(user.visa_categories or ["All categories"])

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F9FAFB;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:680px;margin:32px auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">

    <!-- Header -->
    <div style="background:#1E3A5F;padding:24px 32px;">
      <h1 style="margin:0;color:white;font-size:22px;font-weight:700;">Visapolicy<span style="color:#60A5FA;">.ai</span></h1>
      <p style="margin:4px 0 0;color:#93C5FD;font-size:14px;">Immigration Policy Alert — {today}</p>
    </div>

    <!-- Summary bar -->
    <div style="background:#EFF6FF;padding:16px 32px;border-bottom:1px solid #BFDBFE;">
      <p style="margin:0;color:#1E40AF;font-size:14px;">
        <strong>{len(changes)} rule change{"s" if len(changes) != 1 else ""}</strong> relevant to your profile
        (<strong>{visa_label}</strong>)
        {f'— <span style="color:#DC2626;font-weight:700;">{high_count} high impact</span>' if high_count else ""}
      </p>
    </div>

    <!-- Changes -->
    <div style="padding:24px 32px;">
      {change_blocks}
    </div>

    <!-- Source documents -->
    <div style="padding:0 32px 24px;">
      <h4 style="color:#374151;margin:0 0 8px;">Source Documents</h4>
      <ul style="margin:0;padding-left:20px;color:#6B7280;font-size:13px;line-height:2;">
        {doc_links}
      </ul>
    </div>

    <!-- Footer -->
    <div style="background:#F3F4F6;padding:20px 32px;border-top:1px solid #E5E7EB;">
      <p style="margin:0;font-size:12px;color:#9CA3AF;line-height:1.6;">
        You're receiving this because your profile is subscribed to: <strong>{visa_label}</strong>.<br>
        This is informational only — consult a licensed immigration attorney before taking action.<br>
        <a href="#" style="color:#6B7280;">Manage preferences</a> &nbsp;·&nbsp; <a href="#" style="color:#6B7280;">Unsubscribe</a>
      </p>
    </div>
  </div>
</body>
</html>"""


def build_subject(changes: list[RuleChange], documents: list[PolicyDocument]) -> str:
    high_count = sum(1 for c in changes if c.impact_level == "high")
    prefix = "[HIGH IMPACT] " if high_count > 0 else ""
    if len(documents) == 1:
        title = documents[0].title[:60] + ("..." if len(documents[0].title) > 60 else "")
        return f"{prefix}{title} — {len(changes)} change{'s' if len(changes) != 1 else ''}"
    return f"{prefix}{len(changes)} immigration rule change{'s' if len(changes) != 1 else ''} affecting your profile"


def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F9FAFB;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:480px;margin:48px auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
    <div style="background:#1E3A5F;padding:24px 32px;">
      <h1 style="margin:0;color:white;font-size:20px;font-weight:700;">Visapolicy<span style="color:#60A5FA;">.ai</span></h1>
    </div>
    <div style="padding:32px;">
      <h2 style="margin:0 0 12px;font-size:18px;color:#111827;">Reset your password</h2>
      <p style="margin:0 0 20px;font-size:14px;color:#6B7280;line-height:1.6;">
        We received a request to reset your password. This link expires in 1 hour. If you didn't request this, you can safely ignore this email.
      </p>
      <a href="{reset_url}" style="display:inline-block;background:#1E3A5F;color:white;text-decoration:none;padding:12px 24px;border-radius:8px;font-size:14px;font-weight:600;">Reset password</a>
      <p style="margin:20px 0 0;font-size:12px;color:#9CA3AF;word-break:break-all;">Or copy this link: {reset_url}</p>
    </div>
  </div>
</body>
</html>"""
    try:
        resend.Emails.send({
            "from": settings.resend_from_email,
            "to": [to_email],
            "subject": "Reset your Visapolicy.ai password",
            "html": html,
        })
        logger.info(f"Sent password reset email to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")
        return False


class EmailSender:
    def send_digest(
        self,
        user: User,
        changes: list[RuleChange],
        documents: list[PolicyDocument],
    ) -> bool:
        subject = build_subject(changes, documents)
        html = build_email_html(user, changes, documents)
        try:
            resend.Emails.send({
                "from": settings.resend_from_email,
                "to": [user.email],
                "subject": subject,
                "html": html,
            })
            logger.info(f"Sent digest to {user.email} — {len(changes)} changes")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")
            return False
