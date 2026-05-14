"""
Email notification service.
Uses SMTP when SMTP_USER + SMTP_PASSWORD are configured.
Logs to console in development (no credentials).
"""
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str) -> bool:
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        return await asyncio.to_thread(_send_smtp, to, subject, html_body)
    logger.info("[EMAIL MOCK] To: %s | Subject: %s", to, subject)
    return True


def _send_smtp(to: str, subject: str, html_body: str) -> bool:
    import smtplib
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to, msg.as_string())
        return True
    except Exception as e:
        logger.error("SMTP send failed: %s", e)
        return False


async def send_sla_breach_alert(ticket_number: str, title: str, priority: str, to_email: str) -> None:
    subject = f"[SLA BREACH] Ticket {ticket_number} – {priority.upper()} priority"
    body = f"""
    <h2 style="color:#dc2626">SLA Breach Alert</h2>
    <p>Ticket <strong>{ticket_number}</strong> has breached its SLA deadline.</p>
    <table>
      <tr><td><b>Title:</b></td><td>{title}</td></tr>
      <tr><td><b>Priority:</b></td><td>{priority}</td></tr>
    </table>
    <p>Please resolve this immediately.</p>
    """
    await send_email(to_email, subject, body)


async def send_low_stock_alert(item_name: str, current_stock: int, minimum_stock: int, to_email: str) -> None:
    subject = f"[LOW STOCK] {item_name} – {current_stock} units remaining"
    body = f"""
    <h2 style="color:#d97706">Low Stock Alert</h2>
    <p>Inventory item <strong>{item_name}</strong> is running low.</p>
    <table>
      <tr><td><b>Current Stock:</b></td><td>{current_stock}</td></tr>
      <tr><td><b>Minimum Stock:</b></td><td>{minimum_stock}</td></tr>
    </table>
    <p>Please reorder at your earliest convenience.</p>
    """
    await send_email(to_email, subject, body)


async def send_task_assigned_notification(employee_email: str, employee_name: str,
                                          task_type: str, room_number: str) -> None:
    subject = f"New Task Assigned – {task_type.replace('_', ' ').title()} | Room {room_number}"
    body = f"""
    <h2>New Task Assigned</h2>
    <p>Hi {employee_name},</p>
    <p>A new task has been assigned to you.</p>
    <table>
      <tr><td><b>Task Type:</b></td><td>{task_type.replace('_', ' ').title()}</td></tr>
      <tr><td><b>Room:</b></td><td>{room_number}</td></tr>
    </table>
    <p>Please check the Monitour app for details.</p>
    """
    await send_email(employee_email, subject, body)
