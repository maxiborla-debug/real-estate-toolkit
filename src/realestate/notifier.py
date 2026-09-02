"""Envío del email diario con los matches nuevos, vía SMTP de Gmail.

Requiere una cuenta de Gmail con verificación en 2 pasos activada y una
"contraseña de aplicación" (no la contraseña normal de la cuenta) — ver
docs/DESPLIEGUE.md.
"""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import EmailConfig
from .matching import MatchResult

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _format_property_html(result: MatchResult) -> str:
    p = result.property
    price = f"{p.currency} {p.price:,.0f}" if p.price is not None else "Precio a consultar"

    detalles = []
    if p.ambientes is not None:
        detalles.append(f"{p.ambientes:g} amb.")
    if p.banos is not None:
        detalles.append(f"{p.banos:g} baño/s")
    if p.m2_cubiertos is not None:
        detalles.append(f"{p.m2_cubiertos:g} m²")
    if p.antiguedad_anios is not None:
        detalles.append("a estrenar" if p.antiguedad_anios == 0 else f"{p.antiguedad_anios:g} años")
    detalle_txt = " · ".join(detalles)

    extras = ", ".join(p.amenities + p.exterior) or "-"

    return f"""
    <tr>
      <td style="padding:12px;border-bottom:1px solid #ddd;">
        <div style="font-size:15px;font-weight:bold;">
          <a href="{p.url}">{p.title or p.property_type}</a>
          <span style="float:right;color:#2a7;">{result.score:.0f}% match</span>
        </div>
        <div style="color:#555;font-size:13px;">{p.neighborhood} — {price}</div>
        <div style="color:#555;font-size:13px;">{detalle_txt}</div>
        <div style="color:#888;font-size:12px;">{extras}</div>
        <div style="color:#aaa;font-size:11px;">Fuente: {p.source}</div>
      </td>
    </tr>
    """


def build_email_html(results: list[MatchResult], is_first_run: bool) -> str:
    intro = (
        "Primer escaneo: te mandamos todas las propiedades que matchean tus criterios."
        if is_first_run
        else "Propiedades nuevas de hoy que matchean tus criterios."
    )
    rows = "\n".join(_format_property_html(r) for r in results)
    return f"""
    <html><body style="font-family:sans-serif;">
      <p>{intro}</p>
      <table style="width:100%;border-collapse:collapse;">{rows}</table>
    </body></html>
    """


def send_email(
    results: list[MatchResult],
    is_first_run: bool,
    email_config: EmailConfig,
    smtp_user: str,
    smtp_password: str,
) -> None:
    if not results:
        return  # nada nuevo que matchee: no se manda mail (evita spam vacío todos los días)

    subject = f"{len(results)} propiedades nuevas que matchean tus criterios"
    if is_first_run:
        subject = f"[Primer escaneo] {len(results)} propiedades encontradas"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{email_config.sender_name} <{smtp_user}>"
    msg["To"] = email_config.recipient
    msg.attach(MIMEText(build_email_html(results, is_first_run), "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [email_config.recipient], msg.as_string())
