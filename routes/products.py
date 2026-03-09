import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db.models import db, Product
from services.csv_importer import import_products_from_file

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
def list_products():
    products = Product.query.order_by(Product.used_count.asc(), Product.name.asc()).all()
    return render_template("products/list.html", products=products)


@products_bp.route("/import", methods=["GET", "POST"])
def import_products():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Выберите файл CSV или Excel", "danger")
            return redirect(request.url)

        added, skipped = import_products_from_file(file)
        flash(f"Добавлено: {added}, пропущено (дубли): {skipped}", "success")
        return redirect(url_for("products.list_products"))

    return render_template("products/import.html")


@products_bp.route("/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Продукт удалён", "info")
    return redirect(url_for("products.list_products"))


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form.get("name", product.name).strip() or product.name
        product.url = request.form.get("url", product.url).strip()
        db.session.commit()
        flash("Продукт обновлён", "success")
        return redirect(url_for("products.list_products"))
    return render_template("products/edit.html", product=product)


@products_bp.route("/translate-names", methods=["POST"])
def translate_names():
    """Переводит все названия продуктов на русский через Claude AI."""
    products = Product.query.all()
    names = [p.name for p in products]
    if not names:
        return jsonify({"error": "Нет продуктов"}), 400

    from services.ai_service import _ask
    names_json = json.dumps(names, ensure_ascii=False)
    result_raw = _ask(
        f"Переведи эти названия товаров (витамины, БАД, минералы) на русский язык. "
        f"Сохрани смысл, не добавляй лишних слов. Верни ТОЛЬКО валидный JSON-массив строк "
        f"в том же порядке, без markdown:\n{names_json}",
        max_tokens=2000
    )

    try:
        if "```" in result_raw:
            result_raw = result_raw.split("```")[1]
            if result_raw.startswith("json"):
                result_raw = result_raw[4:]
        translated = json.loads(result_raw)
        if isinstance(translated, list) and len(translated) == len(products):
            for p, new_name in zip(products, translated):
                if new_name and new_name.strip():
                    p.name = new_name.strip()
            db.session.commit()
            return jsonify({"ok": True, "count": len(products)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Неверный формат ответа AI"}), 500


@products_bp.route("/<int:product_id>/set-photo", methods=["POST"])
def set_photo(product_id):
    product = Product.query.get_or_404(product_id)
    filename = request.form.get("filename", "")
    product.photo_filename = filename
    db.session.commit()
    return redirect(url_for("products.list_products"))
