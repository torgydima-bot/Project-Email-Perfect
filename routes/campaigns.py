import json
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db.models import db, Campaign, Contact, Product, MediaFile
import config

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/campaigns")

EMAIL_TYPES = [
    ("PRODUCT", "Продукт выпуска"),
    ("ARTICLE", "Статья о здоровье"),
    ("EXPERT", "Совет специалиста"),
    ("NEWS", "Новости компании"),
    ("PROGRAM", "Индивидуальная программа"),
    ("COMBO", "Комбо / сезонный"),
]


@campaigns_bp.route("/")
def list_campaigns():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template("campaigns/list.html", campaigns=campaigns)


@campaigns_bp.route("/new", methods=["GET", "POST"])
def new_campaign():
    products = Product.query.order_by(Product.used_count.asc(), Product.name.asc()).all()
    media_files = MediaFile.query.order_by(MediaFile.uploaded_at.desc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Введите название кампании", "danger")
            return redirect(request.url)

        content = {
            "greeting_text": request.form.get("greeting_text", ""),
            "product_name": request.form.get("product_name", ""),
            "product_desc": request.form.get("product_desc", ""),
            "product_url": request.form.get("product_url", ""),
            "product_photo": request.form.get("product_photo", ""),
            "article_title": request.form.get("article_title", ""),
            "article_html": request.form.get("article_html", ""),
            "article_image": request.form.get("article_image", ""),
            "news_text": request.form.get("news_text", ""),
            "useful_fact": request.form.get("useful_fact", ""),
            "product_context": request.form.get("product_context", ""),
        }

        campaign = Campaign(
            name=name,
            email_type=request.form.get("email_type", "PRODUCT"),
            subject=request.form.get("subject", ""),
            from_name=request.form.get("from_name", config.FROM_NAME),
            from_email=request.form.get("from_email", config.FROM_EMAIL),
            product_id=int(request.form.get("product_id")) if request.form.get("product_id") else None,
            content_json=json.dumps(content, ensure_ascii=False),
            status="draft",
        )
        db.session.add(campaign)
        db.session.commit()
        flash(f"Кампания «{name}» сохранена", "success")
        return redirect(url_for("campaigns.preview", campaign_id=campaign.id))

    return render_template("campaigns/builder.html",
                           products=products,
                           media_files=media_files,
                           email_types=EMAIL_TYPES,
                           from_name=config.FROM_NAME,
                           from_email=config.FROM_EMAIL)


@campaigns_bp.route("/<int:campaign_id>/edit", methods=["GET", "POST"])
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    products = Product.query.order_by(Product.used_count.asc(), Product.name.asc()).all()
    media_files = MediaFile.query.order_by(MediaFile.uploaded_at.desc()).all()

    try:
        content = json.loads(campaign.content_json or "{}")
    except Exception:
        content = {}

    if request.method == "POST":
        campaign.name = request.form.get("name", "").strip() or campaign.name
        campaign.email_type = request.form.get("email_type", campaign.email_type)
        campaign.subject = request.form.get("subject", "")
        campaign.from_name = request.form.get("from_name", config.FROM_NAME)
        campaign.from_email = request.form.get("from_email", config.FROM_EMAIL)
        pid = request.form.get("product_id")
        campaign.product_id = int(pid) if pid else None

        content = {
            "greeting_text": request.form.get("greeting_text", ""),
            "product_name": request.form.get("product_name", ""),
            "product_desc": request.form.get("product_desc", ""),
            "product_url": request.form.get("product_url", ""),
            "product_photo": request.form.get("product_photo", ""),
            "article_title": request.form.get("article_title", ""),
            "article_html": request.form.get("article_html", ""),
            "article_image": request.form.get("article_image", ""),
            "news_text": request.form.get("news_text", ""),
            "useful_fact": request.form.get("useful_fact", ""),
            "product_context": request.form.get("product_context", ""),
        }
        campaign.content_json = json.dumps(content, ensure_ascii=False)
        db.session.commit()
        flash("Кампания обновлена", "success")
        return redirect(url_for("campaigns.preview", campaign_id=campaign.id))

    return render_template("campaigns/builder.html",
                           campaign=campaign,
                           content=content,
                           products=products,
                           media_files=media_files,
                           email_types=EMAIL_TYPES,
                           from_name=config.FROM_NAME,
                           from_email=config.FROM_EMAIL)


@campaigns_bp.route("/<int:campaign_id>/preview")
def preview(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    total = Contact.query.filter_by(subscribed=True).count()
    gender_counts = {
        "f": Contact.query.filter_by(subscribed=True, gender="f").count(),
        "m": Contact.query.filter_by(subscribed=True, gender="m").count(),
    }
    return render_template("campaigns/preview.html",
                           campaign=campaign,
                           total=total,
                           gender_counts=gender_counts)


@campaigns_bp.route("/<int:campaign_id>/preview-html")
def preview_html(campaign_id):
    """Отдаёт сырой HTML письма для iframe — без экранирования."""
    from flask import Response
    campaign = Campaign.query.get_or_404(campaign_id)
    first_contact = Contact.query.filter_by(subscribed=True).first()
    if not first_contact:
        first_contact = Contact(id=0, email="preview@example.com", first_name="Иван", last_name="Иванов")
    from services.email_builder import build_email_html
    html = build_email_html(campaign, first_contact)
    return Response(html, mimetype="text/html; charset=utf-8")


@campaigns_bp.route("/<int:campaign_id>/send", methods=["POST"])
def send(campaign_id):
    from services.email_service import send_campaign
    gender_filter = request.form.get("gender_filter", "").strip()
    result = send_campaign(campaign_id, gender_filter=gender_filter or None)
    if "error" in result:
        flash(f"Ошибка отправки: {result['error']}", "danger")
    else:
        flash(f"Отправлено: {result['sent']}, ошибок: {result['failed']}", "success")
    return redirect(url_for("campaigns.stats", campaign_id=campaign_id))


@campaigns_bp.route("/<int:campaign_id>/send-test", methods=["POST"])
def send_test(campaign_id):
    test_email = request.form.get("test_email", "").strip()
    test_name = request.form.get("test_name", "").strip()
    if not test_email:
        return jsonify({"error": "Укажите email"}), 400
    from services.email_service import send_test_email
    result = send_test_email(campaign_id, test_email, test_name)
    return jsonify(result)


@campaigns_bp.route("/<int:campaign_id>/stats")
def stats(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    all_logs = campaign.logs.order_by(db.text("sent_at DESC")).all()
    logs = [l for l in all_logs if l.status != "test"]
    test_logs = [l for l in all_logs if l.status == "test"]
    # Последнее открытие для каждого контакта
    from db.models import EmailOpen
    latest_opens = {}
    opens = EmailOpen.query.filter_by(campaign_id=campaign_id)\
        .order_by(EmailOpen.opened_at.desc()).all()
    for o in opens:
        if o.contact_id not in latest_opens:
            latest_opens[o.contact_id] = o
    return render_template("campaigns/stats.html", campaign=campaign,
                           logs=logs, test_logs=test_logs,
                           latest_opens=latest_opens)


@campaigns_bp.route("/<int:campaign_id>/schedule", methods=["POST"])
def schedule_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    scheduled_str = request.form.get("scheduled_at", "").strip()
    if not scheduled_str:
        flash("Выберите дату и время", "danger")
        return redirect(url_for("campaigns.preview", campaign_id=campaign_id))
    try:
        # Пользователь вводит своё местное время → конвертируем в UTC для хранения
        local_dt = datetime.strptime(scheduled_str, "%Y-%m-%dT%H:%M")
        campaign.scheduled_at = local_dt - timedelta(hours=config.TIMEZONE_OFFSET)
    except ValueError:
        flash("Неверный формат даты", "danger")
        return redirect(url_for("campaigns.preview", campaign_id=campaign_id))
    db.session.commit()
    flash(f"Кампания запланирована на {local_dt.strftime('%d.%m.%Y %H:%M')}", "success")
    return redirect(url_for("campaigns.preview", campaign_id=campaign_id))


@campaigns_bp.route("/<int:campaign_id>/unschedule", methods=["POST"])
def unschedule_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.scheduled_at = None
    db.session.commit()
    flash("Расписание снято", "info")
    return redirect(url_for("campaigns.preview", campaign_id=campaign_id))


@campaigns_bp.route("/<int:campaign_id>/delete", methods=["POST"])
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash("Кампания удалена", "info")
    return redirect(url_for("campaigns.list_campaigns"))


# --- AI API endpoints ---

@campaigns_bp.route("/ai/generate-product", methods=["POST"])
def ai_generate_product():
    data = request.json or {}
    product_url = data.get("url", "")
    product_name = data.get("name", "")
    product_context = data.get("context", "")  # текст вставленный вручную

    from services.scraper import fetch_product_text, fetch_product_og_image
    from services.ai_service import generate_product_email

    # Приоритет: ручной контекст > парсинг сайта
    if product_context.strip():
        page_text = product_context
    else:
        page_text = fetch_product_text(product_url) if product_url else ""

    result = generate_product_email(product_name, page_text)

    # og:image с Тильды — публичный CDN URL, работает в любых письмах
    if product_url:
        og_image = fetch_product_og_image(product_url)
        if og_image:
            result["product_image_url"] = og_image

    return jsonify(result)


@campaigns_bp.route("/ai/generate-article", methods=["POST"])
def ai_generate_article():
    data = request.json or {}
    topic = data.get("topic", "")
    from services.ai_service import generate_article
    result = generate_article(topic)
    return jsonify(result)


@campaigns_bp.route("/ai/subject-variants", methods=["POST"])
def ai_subject_variants():
    data = request.json or {}
    topic = data.get("topic", "")
    from services.ai_service import generate_subject_variants
    variants = generate_subject_variants(topic)
    return jsonify({"variants": variants})


@campaigns_bp.route("/ai/generate-photo", methods=["POST"])
def ai_generate_photo():
    data = request.json or {}
    product_name = data.get("name", "")
    topic = data.get("topic", "")
    search_query = product_name or topic
    if not search_query:
        return jsonify({"error": "Укажите название"}), 400

    from services.ai_service import _ask
    from services.image_service import generate_image

    # Claude генерирует English промт для Stable Horde
    if product_name:
        # Фото продукта: баночка/бутылка на красивом природном фоне
        ru_prompt = _ask(
            f"Create an English image prompt (15-25 words) for Stable Diffusion. "
            f"Show a product jar or bottle of '{product_name}' health supplement "
            f"placed in a beautiful natural scene. Choose one random background: "
            f"mountain meadow with wildflowers, tropical beach at sunset, pine forest with sunrays, "
            f"green hills with morning fog, or stone table in a garden. "
            f"Style: cinematic, warm light, shallow depth of field, product photography. "
            f"Return ONLY the prompt, nothing else.",
            max_tokens=80
        )
        if ru_prompt.startswith("[Ошибка") or not ru_prompt.strip():
            ru_prompt = f"glass jar of {product_name} health supplement on mountain meadow, wildflowers, cinematic warm light, product photography"
    else:
        # Фото для статьи: скачиваем с Picsum на сервер (чтобы email-клиенты не блокировали редиректы)
        import hashlib, httpx as _httpx
        seed = int(hashlib.md5(topic.encode()).hexdigest(), 16) % 200 + 1
        picsum_url = f"https://picsum.photos/seed/{seed}/680/440"
        try:
            resp = _httpx.get(picsum_url, follow_redirects=True, timeout=15)
            if resp.status_code == 200:
                upload_dir = Path("static/uploads")
                upload_dir.mkdir(exist_ok=True)
                fname = f"article_{uuid.uuid4().hex[:8]}.jpg"
                (upload_dir / fname).write_bytes(resp.content)
                return jsonify({"filename": fname, "prompt": topic})
        except Exception:
            pass
        return jsonify({"filename": picsum_url, "prompt": topic})

    filename = generate_image(ru_prompt, prompt_en=ru_prompt)
    if filename:
        return jsonify({"filename": filename, "prompt": ru_prompt})
    return jsonify({"error": "Не удалось сгенерировать фото"}), 500
