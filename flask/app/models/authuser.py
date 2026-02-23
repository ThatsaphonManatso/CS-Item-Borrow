from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from app import db
from datetime import datetime


class AuthUser(db.Model, UserMixin):
    __tablename__ = 'auth_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String)
    student_id = db.Column(db.Integer, unique=True)
    email = db.Column(db.String, unique=True)
    gmail = db.Column(db.String, unique=True, default=None)
    is_admin = db.Column(db.Boolean)
    avatar_url=db.Column(db.String, default="https://www.gravatar.com/avatar/205e460b479e2e5b48aec07710c08d50?s=200")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    borrow_requests = db.relationship("BorrowRequest", back_populates="borrower", foreign_keys="[BorrowRequest.borrower_id]")
    verify_requests = db.relationship("BorrowRequest", back_populates="verify_by", foreign_keys="[BorrowRequest.verifier_id]")


    def __init__(self, username, email, avatar_url, student_id=None, gmail=None, is_admin=False):
        self.username = username
        self.student_id = student_id
        self.email = email
        self.gmail = gmail
        self.is_admin = is_admin
        self.avatar_url = avatar_url
