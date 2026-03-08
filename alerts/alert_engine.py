"""
Sistema di alerting via email.
Genera alert per segnali ad alto impatto.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import and_

from config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_RECIPIENTS
from db.models import Signal, Document, Source, Keyword

logger = logging.getLogger("alerts")

# Soglie alert
ALERT_THRESHOLD_IMMEDIATE = 8.0  # strategic_score
ALERT_THRESHOLD_DAILY = 6.0


def check_and_send_alerts(session: Session):
    """Controlla nuovi segnali ad alto impatto e invia alert."""
    since = datetime.utcnow() - timedelta(hours=12)

    # Trova segnali recenti con score alto
    high_signals = (
        session.query(Signal, Document, Source, Keyword)
        .join(Document, Signal.document_id == Document.document_id)
        .join(Source, Document.source_id == Source.source_id)
        .join(Keyword, Signal.keyword_id == Keyword.keyword_id)
        .filter(
            and_(
                Signal.strategic_score >= ALERT_THRESHOLD_DAILY,
                Document.scraped_at >= since,
            )
        )
        .order_by(Signal.strategic_score.desc())
        .limit(20)
        .all()
    )

    if not high_signals:
        logger.info("Nessun alert da inviare.")
        return 0

    # Separa immediati da digest
    immediate = [(s, d, src, kw) for s, d, src, kw in high_signals
                 if s.strategic_score >= ALERT_THRESHOLD_IMMEDIATE]
    digest = [(s, d, src, kw) for s, d, src, kw in high_signals
              if s.strategic_score < ALERT_THRESHOLD_IMMEDIATE]

    # Invia alert immediati
    for signal, doc, source, keyword in immediate:
        _send_immediate_alert(signal, doc, source, keyword)

    # Invia digest se ci sono segnali
    if digest:
        _send_digest(digest)

    logger.info(f"✓ Inviati {len(immediate)} alert immediati + 1 digest ({len(digest)} segnali)")
    return len(immediate) + (1 if digest else 0)


def _send_immediate_alert(signal: Signal, doc: Document, source: Source, keyword: Keyword):
    """Invia email per alert immediato."""
    urgency_emoji = "🔴"
    subject = f"{urgency_emoji} ALERT: {doc.title[:80]}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1B4F72; color: white; padding: 15px 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; font-size: 18px;">{urgency_emoji} High-Impact Signal Detected</h2>
        </div>
        <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
            <h3 style="color: #1B4F72; margin-top: 0;">{doc.title}</h3>

            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <td style="padding: 8px; background: #EBF5FB; font-weight: bold; width: 35%;">Source</td>
                    <td style="padding: 8px; background: #EBF5FB;">{source.source_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Country</td>
                    <td style="padding: 8px;">{doc.country or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background: #EBF5FB; font-weight: bold;">Date</td>
                    <td style="padding: 8px; background: #EBF5FB;">{doc.publish_date or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Type</td>
                    <td style="padding: 8px;">{doc.document_type or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background: #EBF5FB; font-weight: bold;">Keyword Match</td>
                    <td style="padding: 8px; background: #EBF5FB;">{keyword.keyword} (L{keyword.level})</td>
                </tr>
            </table>

            <div style="background: #FEF9E7; border-left: 4px solid #F39C12; padding: 12px; margin: 15px 0;">
                <strong>Scores:</strong>
                Strategic: <strong>{signal.strategic_score:.1f}</strong> |
                Relevance: {signal.relevance_score:.1f} |
                Impact: {signal.impact_score:.1f} |
                Novelty: {signal.novelty_score:.1f}
            </div>

            {f'<p><a href="{doc.url}" style="color: #2E86C1;">View Document →</a></p>' if doc.url else ''}

            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Geopolitical Health Intelligence Dashboard</p>
        </div>
    </div>
    """

    _send_email(subject, html)


def _send_digest(signals_data: List):
    """Invia email digest con segnali del giorno."""
    subject = f"📊 Daily Intelligence Digest ({len(signals_data)} signals)"

    rows = ""
    for signal, doc, source, keyword in signals_data:
        rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">
                <strong>{signal.strategic_score:.1f}</strong>
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">
                <a href="{doc.url}" style="color: #2E86C1; text-decoration: none;">
                    {doc.title[:70]}{'...' if len(doc.title) > 70 else ''}
                </a>
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{source.source_name}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{keyword.keyword}</td>
        </tr>
        """

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
        <div style="background: #2E86C1; color: white; padding: 15px 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0; font-size: 18px;">📊 Daily Intelligence Digest</h2>
            <p style="margin: 5px 0 0; opacity: 0.8;">{datetime.utcnow().strftime('%d %B %Y')}</p>
        </div>
        <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #EBF5FB;">
                        <th style="padding: 10px; text-align: left;">Score</th>
                        <th style="padding: 10px; text-align: left;">Document</th>
                        <th style="padding: 10px; text-align: left;">Source</th>
                        <th style="padding: 10px; text-align: left;">Keyword</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #888; font-size: 12px;">Geopolitical Health Intelligence Dashboard</p>
        </div>
    </div>
    """

    _send_email(subject, html)


def _send_email(subject: str, html_body: str):
    """Invia email via SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD or not ALERT_RECIPIENTS:
        logger.warning("Email non configurata. Alert salvato solo nel DB.")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(ALERT_RECIPIENTS)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, ALERT_RECIPIENTS, msg.as_string())

        logger.info(f"  Email inviata: {subject[:50]}")
    except Exception as e:
        logger.error(f"  Errore invio email: {e}")
