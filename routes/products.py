import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
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


@products_bp.route("/<int:product_id>/set-photo", methods=["POST"])
def set_photo(product_id):
    product = Product.query.get_or_404(product_id)
    filename = request.form.get("filename", "")
    product.photo_filename = filename
    db.session.commit()
    return redirect(url_for("products.list_products"))
