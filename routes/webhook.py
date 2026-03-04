from flask import Blueprint, request, jsonify
from db.models import db, Contact

webhook_bp = Blueprint("webhook", __name__, url_prefix="/webhook")


@webhook_bp.route("/tilda", methods=["POST"])
def tilda():
    """
    Tilda отправляет данные формы при новой подписке.
    Настройка: Форма → Интеграции → Webhook → URL: https://yoursite/webhook/tilda
    """
    data = request.form.to_dict() if request.form else (request.json or {})

    email = (
        data.get("email") or
        data.get("Email") or
        data.get("EMAIL") or ""
    ).strip().lower()

    if not email:
        return jsonify({"error": "no email"}), 400

    name = (
        data.get("name") or data.get("Name") or data.get("NAME") or
        data.get("firstname") or data.get("Firstname") or ""
    ).strip()

    phone = (
        data.get("phone") or data.get("Phone") or data.get("PHONE") or ""
    ).strip()

    # Разбиваем имя на first/last если есть пробел
    parts = name.split(maxsplit=1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""

    existing = Contact.query.filter_by(email=email).first()
    if existing:
        # Обновляем данные если пусто
        if not existing.first_name and first_name:
            existing.first_name = first_name
        if not existing.phone and phone:
            existing.phone = phone
        existing.subscribed = True
        db.session.commit()
        return jsonify({"status": "updated", "id": existing.id})

    contact = Contact(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        source="tilda",
        subscribed=True,
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify({"status": "created", "id": contact.id})
