"""Envío del email diario con los matches nuevos, vía SMTP de Gmail.

Cada perfil (compra/alquiler) manda su propio mail, con su propio asunto y
destinatario — ver `ProfileConfig` en `config.py`.

Requiere una cuenta de Gmail con verificación en 2 pasos activada y una
"contraseña de aplicación" (no la contraseña normal de la cuenta) — ver
docs/DESPLIEGUE.md.
"""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import ProfileConfig
from .matching import MatchResult

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _format_property_html(result: MatchResult) -> str:
    p = result.property
    price = f"{p.currency} {p.price:,.0f}" if p.price is not None else "Precio a consultar"

    detalles = []
    if p.ambientes is not None:
        detalles.append(f"{p.ambientes:g} amb.")
    if p.dormitorios is not None:
        detalles.append(f"{p.dormitorios:g} dorm.")
    if p.banos is not None:
        detalles.append(f"{p.banos:g} baño/s")
    if p.m2 is not None:
        detalles.append(f"{p.m2:g} m²")
    if p.orientacion:
        detalles.append(f"orientación {p.orientacion}")
    if p.antiguedad_anios is not None:
        detalles.append("a estrenar" if p.antiguedad_anios == 0 else f"{p.antiguedad_anios:g} años")
    detalle_txt = " · ".join(detalles)

    extras = ", ".join(p.exterior + (["cochera"] if p.parking else [])) or "-"

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


def build_email_html(results: list[MatchResult], is_first_run: bool, label: str) -> str:
    intro = (
        f"Primer escaneo de {label.lower()}: te mandamos todas las propiedades que matchean tus criterios."
        if is_first_run
        else f"Novedades de hoy en {label.lower()} que matchean tus criterios."
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
    profile: ProfileConfig,
    sender_name: str,
    smtp_user: str,
    smtp_password: str,
) -> None:
    if not results:
        return  # nada nuevo que matchee: no se manda mail (evita spam vacío todos los días)

    subject = f"[{profile.label}] {len(results)} propiedades nuevas que matchean tus criterios"
    if is_first_run:
        subject = f"[{profile.label}] [Primer escaneo] {len(results)} propiedades encontradas"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = profile.recipient
    msg.attach(MIMEText(build_email_html(results, is_first_run, profile.label), "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [profile.recipient], msg.as_string())
