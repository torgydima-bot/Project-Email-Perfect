import json
import os
import config


def build_email_html(campaign, contact) -> str:
    """
    Собирает HTML письма из блоков кампании + данных контакта.
    """
    content = {}
    try:
        content = json.loads(campaign.content_json or "{}")
    except Exception:
        pass

    first_name = contact.first_name or contact.email.split("@")[0]

    # Ссылка отписки
    from itsdangerous import URLSafeSerializer
    s = URLSafeSerializer(config.SECRET_KEY)
    token = s.dumps(contact.id if contact.id else 0)
    unsubscribe_url = f"{config.SITE_URL}/contacts/unsubscribe?token={token}"

    # Фото продукта
    product_image_url = ""
    photo_filename = content.get("product_photo", "")
    if photo_filename:
        product_image_url = f"{config.SITE_URL}/static/uploads/{photo_filename}"

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
        "{{greeting_text}}": content.get("greeting_text", ""),
        "{{product_name}}": content.get("product_name", ""),
        "{{product_desc}}": content.get("product_desc", ""),
        "{{product_url}}": content.get("product_url", "#"),
        "{{product_image_url}}": product_image_url,
        "{{article_title}}": content.get("article_title", ""),
        "{{article_html}}": content.get("article_html", ""),
        "{{news_text}}": content.get("news_text", ""),
        "{{useful_fact}}": content.get("useful_fact", ""),
        "{{unsubscribe_url}}": unsubscribe_url,
        "{{site_url}}": config.SITE_URL,
    }

    html = template
    for key, val in replacements.items():
        html = html.replace(key, str(val) if val else "")

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
            # Удаляем блок целиком
            start_idx = html.find(start_tag)
            end_idx = html.find(end_tag)
            if start_idx != -1 and end_idx != -1:
                html = html[:start_idx] + html[end_idx + len(end_tag):]
        else:
            # Убираем маркеры
            html = html.replace(start_tag, "").replace(end_tag, "")

    return html
