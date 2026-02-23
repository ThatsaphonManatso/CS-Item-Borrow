from app import db
from sqlalchemy_serializer import SerializerMixin


class Category(db.Model, SerializerMixin):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True)
    description = db.Column(db.Text)
    url_img = db.Column(db.String)
    permission_required = db.Column(db.String)

    def __init__(self, name, description, url_img, permission_required):
        self.name = name
        self.description = description
        self.url_img = url_img
        self.permission_required = permission_required

