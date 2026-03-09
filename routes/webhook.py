import logging
from flask import Blueprint, request, jsonify
from db.models import db, Contact

webhook_bp = Blueprint("webhook", __name__, url_prefix="/webhook")
logger = logging.getLogger(__name__)


@webhook_bp.route("/tilda", methods=["POST"])
def tilda():
    data = request.form.to_dict() if request.form else (request.json or {})

    # Tilda отправляет {"test":"test"} при сохранении webhook — просто подтверждаем
    if data == {"test": "test"} or data.get("test"):
        return jsonify({"status": "ok"}), 200

    logger.warning(f"Tilda webhook data: {data}")

    # Ищем email по всем ключам (любой регистр)
    email = ""
    for key, val in data.items():
        if "email" in key.lower() or "mail" in key.lower() or "@" in str(val):
            candidate = str(val).strip().lower()
            if "@" in candidate:
                email = candidate
                break
    # Fallback: ищем значение с @ среди всех значений
    if not email:
        for val in data.values():
            if "@" in str(val):
                email = str(val).strip().lower()
                break

    if not email:
        logger.warning(f"No email found in: {data}")
        return jsonify({"error": "no email", "received": data}), 400

    # Ищем имя по всем ключам
    name = ""
    for key in data:
        if any(k in key.lower() for k in ["name", "fname", "имя", "fio"]):
            name = str(data[key]).strip()
            break

    # Ищем телефон
    phone = ""
    for key in data:
        if any(k in key.lower() for k in ["phone", "tel", "телефон"]):
            phone = str(data[key]).strip()
            break

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
