import os
from flask import Flask
from db.models import db
import config


def _send_scheduled_campaigns(app):
    """Проверяет запланированные кампании и отправляет те, чьё время пришло."""
    from datetime import datetime
    with app.app_context():
        from db.models import Campaign
        from services.email_service import send_campaign
        due = Campaign.query.filter(
            Campaign.scheduled_at <= datetime.utcnow(),
            Campaign.scheduled_at.isnot(None),
            Campaign.status == "draft",
        ).all()
        for campaign in due:
            try:
                send_campaign(campaign.id)
            except Exception as e:
                app.logger.error(f"Ошибка авто-отправки кампании {campaign.id}: {e}")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{config.DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    db.init_app(app)

    # Jinja2-фильтр: UTC → локальное время пользователя (UTC+TIMEZONE_OFFSET)
    from datetime import timedelta
    def _local_dt(dt):
        if dt is None:
            return ""
        return dt + timedelta(hours=config.TIMEZONE_OFFSET)
    app.jinja_env.filters["local_dt"] = _local_dt

    # Регистрация роутов
    from routes.contacts import contacts_bp
    from routes.products import products_bp
    from routes.campaigns import campaigns_bp
    from routes.calendar import calendar_bp
    from routes.media import media_bp
    from routes.webhook import webhook_bp
    from routes.tracking import tracking_bp

    app.register_blueprint(contacts_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(tracking_bp)

    # Главная страница — редирект на контент-календарь
    from flask import redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("campaigns.list_campaigns"))

    # Запускаем планировщик (только в основном процессе, не в reloader-дочернем)
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            _send_scheduled_campaigns,
            trigger="interval",
            minutes=1,
            args=[app],
            id="send_scheduled",
            replace_existing=True,
        )
        scheduler.start()

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
