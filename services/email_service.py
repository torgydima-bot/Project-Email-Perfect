import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from itsdangerous import URLSafeSerializer

import config
from db.models import db, Contact, Campaign, CampaignLog
from services.email_builder import build_email_html


def _unsubscribe_url(contact_id: int) -> str:
    s = URLSafeSerializer(config.SECRET_KEY)
    token = s.dumps(contact_id)
    return f"{config.SITE_URL}/contacts/unsubscribe?token={token}"


def send_campaign(campaign_id: int):
    """
    Отправляет кампанию всем подписанным контактам.
    Батчи по 50 писем, пауза 1 сек между батчами.
    """
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return {"error": "Campaign not found"}

    campaign.status = "sending"
    db.session.commit()

    contacts = Contact.query.filter_by(subscribed=True).all()

    # Уже отправленным — пропускаем
    already_sent = {
        log.contact_id
        for log in CampaignLog.query.filter_by(campaign_id=campaign_id, status="sent").all()
    }

    total_sent = 0
    total_failed = 0

    from_name = campaign.from_name or config.FROM_NAME
    from_email = campaign.from_email or config.FROM_EMAIL

    try:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)

        batch = []
        for contact in contacts:
            if contact.id in already_sent:
                continue
            batch.append(contact)
            if len(batch) >= 50:
                _send_batch(server, campaign, batch, from_name, from_email)
                total_sent += len(batch)
                batch = []
                time.sleep(1)

        if batch:
            sent, failed = _send_batch(server, campaign, batch, from_name, from_email)
            total_sent += sent
            total_failed += failed

        server.quit()
    except Exception as e:
        campaign.status = "draft"
        db.session.commit()
        return {"error": str(e)}

    campaign.status = "done"
    campaign.sent_at = datetime.utcnow()
    if campaign.product_id:
        from db.models import Product
        p = Product.query.get(campaign.product_id)
        if p:
            p.used_count += 1
    db.session.commit()

    return {"sent": total_sent, "failed": total_failed}


def _send_batch(server, campaign, contacts, from_name, from_email):
    sent = failed = 0
    for contact in contacts:
        try:
            html = build_email_html(campaign, contact)
            subject = _personalize(campaign.subject, contact)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = contact.email
            msg["List-Unsubscribe"] = f"<{_unsubscribe_url(contact.id)}>"

            msg.attach(MIMEText(html, "html", "utf-8"))
            server.sendmail(from_email, contact.email, msg.as_string())

            log = CampaignLog(
                campaign_id=campaign.id,
                contact_id=contact.id,
                status="sent",
                sent_at=datetime.utcnow(),
            )
            db.session.add(log)
            sent += 1
        except Exception as e:
            log = CampaignLog(
                campaign_id=campaign.id,
                contact_id=contact.id,
                status="failed",
                error_msg=str(e)[:500],
            )
            db.session.add(log)
            failed += 1

    db.session.commit()
    return sent, failed


def _personalize(text: str, contact: Contact) -> str:
    return text.replace("{{first_name}}", contact.first_name or "") \
               .replace("{{last_name}}", contact.last_name or "") \
               .replace("{{email}}", contact.email or "")


def send_test_email(campaign_id: int, test_email: str):
    """Отправляет тестовое письмо на указанный адрес."""
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return {"error": "Campaign not found"}

    # Создаём временный контакт для предпросмотра
    fake_contact = Contact(
        email=test_email,
        first_name="Тест",
        last_name="Тестов",
    )
    html = build_email_html(campaign, fake_contact)

    from_name = campaign.from_name or config.FROM_NAME
    from_email = campaign.from_email or config.FROM_EMAIL

    try:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[ТЕСТ] {campaign.subject}"
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = test_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        server.sendmail(from_email, test_email, msg.as_string())
        server.quit()
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}
