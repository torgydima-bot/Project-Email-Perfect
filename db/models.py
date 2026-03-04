from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100), default="")
    last_name = db.Column(db.String(100), default="")
    phone = db.Column(db.String(50), default="")
    source = db.Column(db.String(50), default="manual")  # manual | tilda
    subscribed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship("CampaignLog", back_populates="contact", lazy="dynamic")

    def display_name(self):
        if self.first_name:
            return self.first_name
        return self.email.split("@")[0]


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), default="")
    photo_filename = db.Column(db.String(255), default="")
    used_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campaigns = db.relationship("Campaign", back_populates="product", lazy="dynamic")


class Campaign(db.Model):
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email_type = db.Column(db.String(50), default="PRODUCT")
    # PRODUCT | ARTICLE | EXPERT | NEWS | PROGRAM | COMBO

    subject = db.Column(db.String(255), default="")
    from_name = db.Column(db.String(100), default="")
    from_email = db.Column(db.String(255), default="")

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    product = db.relationship("Product", back_populates="campaigns")

    # JSON со всеми блоками письма
    content_json = db.Column(db.Text, default="{}")

    status = db.Column(db.String(20), default="draft")  # draft | sending | done
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship("CampaignLog", back_populates="campaign", lazy="dynamic")

    def sent_count(self):
        return self.logs.filter_by(status="sent").count()

    def failed_count(self):
        return self.logs.filter_by(status="failed").count()

    def total_count(self):
        return self.logs.count()


class CampaignLog(db.Model):
    __tablename__ = "campaign_logs"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending | sent | failed
    error_msg = db.Column(db.Text, default="")
    sent_at = db.Column(db.DateTime, nullable=True)

    campaign = db.relationship("Campaign", back_populates="logs")
    contact = db.relationship("Contact", back_populates="logs")


class MediaFile(db.Model):
    __tablename__ = "media_files"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), default="")
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
