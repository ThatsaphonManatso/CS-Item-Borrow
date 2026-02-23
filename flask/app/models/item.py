from app import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime

from .category import Category

class Item(db.Model, SerializerMixin):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    status = db.Column(db.String, default="Available")  # Available / Unavailable / Repairing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("Category")

    def __init__(self, category_id):
        self.category_id = category_id

    def update_status(self, status):
        self.status = status
