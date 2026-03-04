import os
from flask import Flask
from db.models import db
import config


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{config.DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    db.init_app(app)

    # Регистрация роутов
    from routes.contacts import contacts_bp
    from routes.products import products_bp
    from routes.campaigns import campaigns_bp
    from routes.calendar import calendar_bp
    from routes.media import media_bp
    from routes.webhook import webhook_bp

    app.register_blueprint(contacts_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(webhook_bp)

    # Главная страница — редирект на контент-календарь
    from flask import redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("campaigns.list_campaigns"))

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
