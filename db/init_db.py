import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from db.models import db

app = create_app()
with app.app_context():
    db.create_all()
    print("База данных создана: email_perfect.db")
