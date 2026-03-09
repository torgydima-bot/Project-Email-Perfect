import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from db.models import db, MediaFile

media_bp = Blueprint("media", __name__, url_prefix="/media")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@media_bp.route("/")
def library():
    files = MediaFile.query.order_by(MediaFile.uploaded_at.desc()).all()
    return render_template("media/library.html", files=files)


@media_bp.route("/upload", methods=["POST"])
def upload():
    uploaded_files = request.files.getlist("files")
    count = 0
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            original = secure_filename(file.filename)
            ext = original.rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
            file.save(save_path)
            media = MediaFile(filename=unique_name, original_name=original)
            db.session.add(media)
            count += 1
    db.session.commit()
    flash(f"Загружено файлов: {count}", "success")
    return redirect(url_for("media.library"))


@media_bp.route("/<int:file_id>/delete", methods=["POST"])
def delete_file(file_id):
    media = MediaFile.query.get_or_404(file_id)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], media.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(media)
    db.session.commit()
    flash("Файл удалён", "info")
    return redirect(url_for("media.library"))


@media_bp.route("/upload-single", methods=["POST"])
def upload_single():
    """JSON-загрузка одного файла (для JS fetch в конструкторе)."""
    file = request.files.get("file")
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Недопустимый файл"}), 400
    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)
    media = MediaFile(filename=unique_name, original_name=original)
    db.session.add(media)
    db.session.commit()
    return jsonify({"filename": unique_name})


@media_bp.route("/api/list")
def api_list():
    """JSON список файлов для выбора в конструкторе кампании."""
    files = MediaFile.query.order_by(MediaFile.uploaded_at.desc()).all()
    return jsonify([
        {"id": f.id, "filename": f.filename, "original_name": f.original_name}
        for f in files
    ])
