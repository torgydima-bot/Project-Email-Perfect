import io
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db.models import db, Contact
from services.csv_importer import import_contacts_from_file

contacts_bp = Blueprint("contacts", __name__, url_prefix="/contacts")


@contacts_bp.route("/")
def list_contacts():
    q = request.args.get("q", "").strip()
    query = Contact.query
    if q:
        query = query.filter(
            (Contact.email.ilike(f"%{q}%")) |
            (Contact.first_name.ilike(f"%{q}%")) |
            (Contact.last_name.ilike(f"%{q}%"))
        )
    contacts = query.order_by(Contact.created_at.desc()).all()
    total = Contact.query.count()
    subscribed = Contact.query.filter_by(subscribed=True).count()
    return render_template("contacts/list.html", contacts=contacts, q=q,
                           total=total, subscribed=subscribed)


@contacts_bp.route("/import", methods=["GET", "POST"])
def import_contacts():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Выберите файл CSV или Excel", "danger")
            return redirect(request.url)

        added, skipped, errors = import_contacts_from_file(file)
        flash(f"Добавлено: {added}, пропущено (дубли): {skipped}, ошибок: {errors}", "success")
        return redirect(url_for("contacts.list_contacts"))

    return render_template("contacts/import.html")


@contacts_bp.route("/<int:contact_id>/toggle-subscribe", methods=["POST"])
def toggle_subscribe(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    contact.subscribed = not contact.subscribed
    db.session.commit()
    return redirect(url_for("contacts.list_contacts"))


@contacts_bp.route("/<int:contact_id>/delete", methods=["POST"])
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash("Контакт удалён", "info")
    return redirect(url_for("contacts.list_contacts"))


@contacts_bp.route("/unsubscribe")
def unsubscribe():
    from itsdangerous import URLSafeSerializer, BadSignature
    import config
    token = request.args.get("token", "")
    s = URLSafeSerializer(config.SECRET_KEY)
    try:
        contact_id = s.loads(token)
        contact = Contact.query.get(contact_id)
        if contact:
            contact.subscribed = False
            db.session.commit()
            return render_template("contacts/unsubscribed.html", contact=contact)
    except BadSignature:
        pass
    return "Недействительная ссылка", 400
