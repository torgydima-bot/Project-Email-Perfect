import base64
from datetime import datetime
from flask import Blueprint, request, Response
from itsdangerous import URLSafeSerializer, BadSignature
from db.models import db, EmailOpen
import config

tracking_bp = Blueprint("tracking", __name__)

# 1x1 прозрачный GIF
_PIXEL_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


def _detect_device(ua: str) -> str:
    ua_lower = ua.lower()
    # Почтовые прокси — не боты, считаем как мобильное (обычно открывают на телефоне)
    email_proxies = ("googleimageproxy", "yandeximage", "yamail", "mail.ru",
                     "outlookmobile", "yahoo! slurp")
    if any(x in ua_lower for x in email_proxies):
        return "mobile"
    # Настоящие боты
    bot_markers = ("spider", "crawl", "preview", "fetch", "headless",
                   "phantom", "slurp", "semrush", "ahref")
    if any(x in ua_lower for x in bot_markers):
        return "bot"
    # "bot" как отдельное слово, но не в составе "robot" от email-клиента
    if "bot" in ua_lower and not any(x in ua_lower for x in email_proxies):
        import re
        if re.search(r'\bbot\b', ua_lower):
            return "bot"
    if any(x in ua_lower for x in ("ipad", "tablet")):
        return "tablet"
    if any(x in ua_lower for x in ("mobile", "android", "iphone", "ipod", "windows phone")):
        return "mobile"
    return "desktop"


@tracking_bp.route("/track/open/<token>")
def track_open(token):
    s = URLSafeSerializer(config.SECRET_KEY)
    try:
        data = s.loads(token)
        campaign_id = data.get("c")
        contact_id = data.get("u")
        ua = request.headers.get("User-Agent", "")
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        open_log = EmailOpen(
            campaign_id=campaign_id,
            contact_id=contact_id,
            user_agent=ua[:500],
            device_type=_detect_device(ua),
            ip_address=ip[:50],
        )
        db.session.add(open_log)
        db.session.commit()
    except (BadSignature, Exception):
        pass

    return Response(
        _PIXEL_GIF,
        mimetype="image/gif",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )
