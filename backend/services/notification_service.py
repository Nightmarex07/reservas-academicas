import logging
import asyncio
from typing import Optional
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


async def _send_email(to: str, subject: str, html_body: str) -> None:
    """Send HTML email via SMTP with exponential backoff retries. Spec: NOT-05."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=settings.SMTP_TLS,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
            )
            logger.info("Email sent to %s: %s", to, subject)
            return
        except Exception as exc:
            logger.warning("Email send failed for %s (non-fatal): %s", to, exc)
            break


def _html(title: str, body: str) -> str:
    return f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:auto">
    <h2 style="color:#1a56db">{title}</h2>
    <div>{body}</div>
    <hr/><p style="color:#888;font-size:12px">{settings.APP_NAME}</p>
    </body></html>
    """


async def send_reservation_created(
    to: str, user_name: str, reservation_id: int,
    space_name: str, start_time, end_time
) -> None:
    """Spec: NOT-01."""
    body = f"""
    <p>Hola <b>{user_name}</b>,</p>
    <p>Tu solicitud de reserva ha sido recibida.</p>
    <table style="border-collapse:collapse">
    <tr><td><b>Referencia:</b></td><td>#{reservation_id}</td></tr>
    <tr><td><b>Espacio:</b></td><td>{space_name}</td></tr>
    <tr><td><b>Inicio:</b></td><td>{start_time}</td></tr>
    <tr><td><b>Fin:</b></td><td>{end_time}</td></tr>
    <tr><td><b>Estado:</b></td><td>Pendiente de aprobación</td></tr>
    </table>
    """
    await _send_email(to, f"Solicitud recibida — Reserva #{reservation_id}", _html("Solicitud de Reserva Recibida", body))


async def send_reservation_approved(
    to: str, user_name: str, reservation_id: int,
    space_name: str, start_time, end_time
) -> None:
    """Spec: NOT-02."""
    body = f"""
    <p>Hola <b>{user_name}</b>,</p>
    <p>Tu reserva ha sido <b style="color:green">aprobada</b>.</p>
    <table style="border-collapse:collapse">
    <tr><td><b>Referencia:</b></td><td>#{reservation_id}</td></tr>
    <tr><td><b>Espacio:</b></td><td>{space_name}</td></tr>
    <tr><td><b>Inicio:</b></td><td>{start_time}</td></tr>
    <tr><td><b>Fin:</b></td><td>{end_time}</td></tr>
    </table>
    <p>Recuerda llegar puntual y dejar el espacio en buenas condiciones.</p>
    """
    await _send_email(to, f"Reserva #{reservation_id} Aprobada", _html("¡Reserva Aprobada!", body))


async def send_reservation_rejected(
    to: str, user_name: str, reservation_id: int,
    space_name: str, reason: str
) -> None:
    """Spec: NOT-03."""
    body = f"""
    <p>Hola <b>{user_name}</b>,</p>
    <p>Tu solicitud de reserva ha sido <b style="color:red">rechazada</b>.</p>
    <table style="border-collapse:collapse">
    <tr><td><b>Referencia:</b></td><td>#{reservation_id}</td></tr>
    <tr><td><b>Espacio:</b></td><td>{space_name}</td></tr>
    <tr><td><b>Motivo:</b></td><td>{reason}</td></tr>
    </table>
    <p>Puedes realizar una nueva solicitud para otro horario disponible.</p>
    """
    await _send_email(to, f"Reserva #{reservation_id} Rechazada", _html("Solicitud Rechazada", body))


async def send_reservation_cancelled(
    to: str, user_name: str, reservation_id: int,
    space_name: str, by_admin: bool = False, reason: Optional[str] = None
) -> None:
    """Spec: NOT-04."""
    source = "administrativamente" if by_admin else "por ti"
    reason_text = f"<p><b>Motivo:</b> {reason}</p>" if reason else ""
    body = f"""
    <p>Hola <b>{user_name}</b>,</p>
    <p>Tu reserva ha sido <b>cancelada</b> {source}.</p>
    <table style="border-collapse:collapse">
    <tr><td><b>Referencia:</b></td><td>#{reservation_id}</td></tr>
    <tr><td><b>Espacio:</b></td><td>{space_name}</td></tr>
    </table>
    {reason_text}
    """
    await _send_email(to, f"Reserva #{reservation_id} Cancelada", _html("Reserva Cancelada", body))
