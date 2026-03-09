import json
import os
import re
import config


def _make_preheader(content: dict, first_name: str) -> str:
    """Генерирует preheader — текст превью письма (до 100 символов)."""
    greeting = content.get("greeting_text", "")
    # Убираем HTML-теги если есть
    text = re.sub(r"<[^>]+>", " ", greeting).strip()
    text = re.sub(r"\s+", " ", text)
    # Персонализируем
    text = text.replace("{{first_name}}", first_name).replace("{first_name}", first_name)
    if not text:
        article_title = content.get("article_title", "")
        product_name = content.get("product_name", "")
        text = article_title or product_name or ""
    return text[:110]


def build_email_html(campaign, contact) -> str:
    """
    Собирает HTML письма из блоков кампании + данных контакта.
    """
    content = {}
    try:
        content = json.loads(campaign.content_json or "{}")
    except Exception:
        pass

    first_name = contact.first_name or "Друг"

    # Ссылка отписки
    from itsdangerous import URLSafeSerializer
    s = URLSafeSerializer(config.SECRET_KEY)
    token = s.dumps(contact.id if contact.id else 0)
    public_url = getattr(config, "PUBLIC_URL", config.SITE_URL)
    unsubscribe_url = f"{public_url}/contacts/unsubscribe?token={token}"

    # Базовый URL для статических файлов (HTTPS-compatible)
    static_base = getattr(config, "STATIC_BASE_URL", config.SITE_URL + "/static")

    # Фото продукта
    product_image_url = ""
    photo_filename = content.get("product_photo", "")
    if photo_filename:
        if photo_filename.startswith("http"):
            product_image_url = photo_filename
        else:
            product_image_url = f"{static_base}/uploads/{photo_filename}"

    # Стиль шапки (фон)
    header_bg_image = getattr(config, "HEADER_BG_IMAGE", "")
    if header_bg_image:
        if not header_bg_image.startswith("http"):
            header_bg_image = f"{static_base}/uploads/{header_bg_image}"
        header_bg_style = (
            f"background:linear-gradient(135deg,rgba(45,106,79,0.05) 0%,rgba(64,145,108,0.05) 100%),"
            f"url('{header_bg_image}') center/cover no-repeat;"
        )
    else:
        header_bg_style = "background:linear-gradient(135deg,#2d6a4f 0%,#40916c 100%);"

    # Блок менеджера / Telegram (личный)
    manager_block = ""
    if config.MANAGER_TELEGRAM or config.TELEGRAM_URL:
        tg_link = config.TELEGRAM_URL or f"https://t.me/{config.MANAGER_TELEGRAM.lstrip('@')}"
        manager_name = config.MANAGER_NAME or "Менеджер"
        manager_block = (
            f'<tr><td style="padding:0 40px 16px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="background:linear-gradient(135deg,#e8f5e9 0%,#f1f8e9 100%);'
            f'border-radius:12px;overflow:hidden;">'
            f'<tr><td style="padding:20px 28px;">'
            f'<p style="margin:0 0 6px;font-size:13px;color:#2d6a4f;font-weight:700;">'
            f'💬 Остались вопросы? Пишите нам!</p>'
            f'<p style="margin:0 0 12px;font-size:13px;color:#495057;line-height:1.5;">'
            f'Менеджер компании <strong>{manager_name}</strong> ответит на любой вопрос о продуктах и поможет подобрать подходящий.</p>'
            f'<a href="{tg_link}" '
            f'style="display:inline-block;background:#229ED9;color:#ffffff;text-decoration:none;'
            f'padding:10px 22px;border-radius:8px;font-size:13px;font-weight:600;">'
            f'✈ Написать в Telegram</a>'
            f'</td></tr></table></td></tr>'
        )

    # Блок Telegram-канала
    telegram_channel_block = ""
    channel_url = getattr(config, "TELEGRAM_CHANNEL_URL", "")
    if channel_url:
        telegram_channel_block = (
            f'<tr><td style="padding:0 40px 24px;text-align:center;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="background:linear-gradient(135deg,#e3f2fd 0%,#e8eaf6 100%);'
            f'border-radius:12px;overflow:hidden;">'
            f'<tr><td style="padding:20px 28px;text-align:center;">'
            f'<p style="margin:0 0 6px;font-size:22px;">📣</p>'
            f'<p style="margin:0 0 4px;font-size:14px;color:#1565c0;font-weight:700;">'
            f'Наш Telegram-канал</p>'
            f'<p style="margin:0 0 14px;font-size:13px;color:#495057;">'
            f'Подпишитесь, чтобы быть в курсе акций, новинок и советов по здоровью</p>'
            f'<a href="{channel_url}" '
            f'style="display:inline-block;background:#229ED9;color:#ffffff;text-decoration:none;'
            f'padding:10px 28px;border-radius:8px;font-size:13px;font-weight:600;">'
            f'✈ Подписаться на канал</a>'
            f'</td></tr></table></td></tr>'
        )

    # Фото статьи
    article_image_block = ""
    article_photo = content.get("article_image", "")
    if article_photo:
        # Если это picsum redirect URL — скачиваем на сервер (email-клиенты не следуют редиректам)
        if "picsum.photos" in article_photo and not "fastly.picsum.photos" in article_photo:
            try:
                import httpx as _httpx, uuid as _uuid, pathlib as _pl
                r = _httpx.get(article_photo, follow_redirects=True, timeout=10)
                if r.status_code == 200:
                    fname = f"article_{_uuid.uuid4().hex[:8]}.jpg"
                    up_dir = _pl.Path(config.UPLOAD_FOLDER)
                    up_dir.mkdir(exist_ok=True)
                    (up_dir / fname).write_bytes(r.content)
                    article_photo = fname
            except Exception:
                pass
        art_img_url = article_photo if article_photo.startswith("http") else f"{static_base}/uploads/{article_photo}"
        article_image_block = (
            f'<tr><td style="padding:0;">'
            f'<img src="{art_img_url}" alt="" '
            f'style="width:100%;max-height:220px;object-fit:cover;display:block;" '
            f'onerror="this.style.display=\'none\'">'
            f'</td></tr>'
        )

    # Tracking pixel
    tracking_pixel = ""
    if contact.id:
        from itsdangerous import URLSafeSerializer as _US
        _s = _US(config.SECRET_KEY)
        _token = _s.dumps({"c": campaign.id, "u": contact.id})
        tracking_pixel = (
            f'<img src="{public_url}/track/open/{_token}" '
            f'width="1" height="1" style="display:block;width:1px;height:1px;" alt="">'
        )

    # Читаем мастер-шаблон
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "email_html", "base_email.html"
    )
    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    # Подстановка переменных
    replacements = {
        "{{first_name}}": first_name,
        "{{last_name}}": contact.last_name or "",
        "{{email}}": contact.email,
        "{{company_name}}": config.FROM_NAME,
        "{{header_bg_style}}": header_bg_style,
        "{{header_bg_image_url}}": header_bg_image if header_bg_image else "",
        "{{greeting_text}}": content.get("greeting_text", ""),
        "{{product_name}}": content.get("product_name", ""),
        "{{product_desc}}": content.get("product_desc", ""),
        "{{product_url}}": content.get("product_url", "#"),
        "{{product_image_url}}": product_image_url,
        "{{article_title}}": content.get("article_title", ""),
        "{{article_html}}": content.get("article_html", ""),
        "{{news_text}}": content.get("news_text", ""),
        "{{useful_fact}}": content.get("useful_fact", ""),
        "{{article_image_block}}": article_image_block,
        "{{manager_block}}": manager_block,
        "{{telegram_channel_block}}": telegram_channel_block,
        "{{unsubscribe_url}}": unsubscribe_url,
        "{{site_url}}": getattr(config, "COMPANY_SITE_URL", config.SITE_URL),
        "{{tracking_pixel}}": tracking_pixel,
        "{{preheader}}": _make_preheader(content, first_name),
    }

    html = template
    for key, val in replacements.items():
        html = html.replace(key, str(val) if val else "")

    # Второй проход: заменяем {{first_name}} внутри вставленного AI-контента
    html = html.replace("{{first_name}}", first_name)
    html = html.replace("{{last_name}}", contact.last_name or "")

    # Скрываем пустые блоки
    html = _hide_empty_blocks(html, content)

    return html


def _hide_empty_blocks(html: str, content: dict) -> str:
    """Убирает блоки без контента."""
    blocks = {
        "<!-- BLOCK_ARTICLE_START -->": "<!-- BLOCK_ARTICLE_END -->",
        "<!-- BLOCK_PRODUCT_START -->": "<!-- BLOCK_PRODUCT_END -->",
        "<!-- BLOCK_NEWS_START -->": "<!-- BLOCK_NEWS_END -->",
    }

    checks = {
        "<!-- BLOCK_ARTICLE_START -->": content.get("article_html", "").strip(),
        "<!-- BLOCK_PRODUCT_START -->": content.get("product_name", "").strip(),
        "<!-- BLOCK_NEWS_START -->": content.get("news_text", "").strip(),
    }

    for start_tag, end_tag in blocks.items():
        if not checks.get(start_tag):
            start_idx = html.find(start_tag)
            end_idx = html.find(end_tag)
            if start_idx != -1 and end_idx != -1:
                html = html[:start_idx] + html[end_idx + len(end_tag):]
        else:
            html = html.replace(start_tag, "").replace(end_tag, "")

    return html
