import json
from datetime import datetime
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
            "news_text": request.form.get("news_text", ""),
            "useful_fact": request.form.get("useful_fact", ""),
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
            "news_text": request.form.get("news_text", ""),
            "useful_fact": request.form.get("useful_fact", ""),
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
    first_contact = Contact.query.filter_by(subscribed=True).first()
    if not first_contact:
        first_contact = Contact(id=0, email="preview@example.com", first_name="Иван", last_name="Иванов")

    from services.email_builder import build_email_html
    html = build_email_html(campaign, first_contact)
    total = Contact.query.filter_by(subscribed=True).count()
    return render_template("campaigns/preview.html",
                           campaign=campaign,
                           preview_html=html,
                           total=total)


@campaigns_bp.route("/<int:campaign_id>/send", methods=["POST"])
def send(campaign_id):
    from services.email_service import send_campaign
    result = send_campaign(campaign_id)
    if "error" in result:
        flash(f"Ошибка отправки: {result['error']}", "danger")
    else:
        flash(f"Отправлено: {result['sent']}, ошибок: {result['failed']}", "success")
    return redirect(url_for("campaigns.stats", campaign_id=campaign_id))


@campaigns_bp.route("/<int:campaign_id>/send-test", methods=["POST"])
def send_test(campaign_id):
    test_email = request.form.get("test_email", "").strip()
    if not test_email:
        return jsonify({"error": "Укажите email"}), 400
    from services.email_service import send_test_email
    result = send_test_email(campaign_id, test_email)
    return jsonify(result)


@campaigns_bp.route("/<int:campaign_id>/stats")
def stats(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    logs = campaign.logs.order_by(db.text("sent_at DESC")).all()
    return render_template("campaigns/stats.html", campaign=campaign, logs=logs)


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

    from services.scraper import fetch_product_text
    from services.ai_service import generate_product_email

    page_text = fetch_product_text(product_url) if product_url else ""
    result = generate_product_email(product_name, page_text)
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
