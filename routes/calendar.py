from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db.models import db, Campaign, Product

calendar_bp = Blueprint("calendar", __name__, url_prefix="/calendar")

EMAIL_TYPES = [
    ("PRODUCT", "Продукт выпуска"),
    ("ARTICLE", "Статья о здоровье"),
    ("EXPERT", "Совет специалиста"),
    ("NEWS", "Новости компании"),
    ("PROGRAM", "Индивидуальная программа"),
    ("COMBO", "Комбо / сезонный"),
]


@calendar_bp.route("/")
def index():
    upcoming = (
        Campaign.query
        .filter(Campaign.scheduled_at >= datetime.utcnow())
        .order_by(Campaign.scheduled_at.asc())
        .limit(14)
        .all()
    )
    past = (
        Campaign.query
        .filter(Campaign.status == "done")
        .order_by(Campaign.sent_at.desc())
        .limit(10)
        .all()
    )
    products = Product.query.order_by(Product.used_count.asc()).all()
    return render_template("calendar/index.html",
                           upcoming=upcoming, past=past,
                           products=products, email_types=EMAIL_TYPES)


@calendar_bp.route("/add", methods=["POST"])
def add():
    name = request.form.get("name", "").strip()
    email_type = request.form.get("email_type", "PRODUCT")
    product_id = request.form.get("product_id") or None
    scheduled_str = request.form.get("scheduled_at", "")

    if not name:
        flash("Введите название кампании", "danger")
        return redirect(url_for("calendar.index"))

    scheduled_at = None
    if scheduled_str:
        try:
            scheduled_at = datetime.strptime(scheduled_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    campaign = Campaign(
        name=name,
        email_type=email_type,
        product_id=int(product_id) if product_id else None,
        scheduled_at=scheduled_at,
        status="draft",
    )
    db.session.add(campaign)
    db.session.commit()
    flash(f"Кампания «{name}» добавлена в план", "success")
    return redirect(url_for("calendar.index"))
