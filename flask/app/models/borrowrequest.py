from app import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from app.models.item import Item 

borrow_request_items = db.Table('borrow_request_items',
    db.Column('borrow_request_id', db.Integer, db.ForeignKey('borrow_requests.id'), primary_key=True),
    db.Column('item_id', db.Integer, db.ForeignKey('items.id'), primary_key=True)
)

class BorrowRequest(db.Model, SerializerMixin):
    __tablename__ = 'borrow_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('auth_users.id'))  # Foreign key to AuthUser
    status = db.Column(db.String, default="Pending")  # Pending / Reject / Approve / Returned    
    verifier_id = db.Column(db.Integer, db.ForeignKey('auth_users.id'))  # Foreign key to AuthUser
    verify_status = db.Column(db.String, default="Pending")
    borrow_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship("Item", secondary=borrow_request_items, backref=db.backref('borrow_requests', lazy='dynamic'))

    borrower = db.relationship("AuthUser", back_populates="borrow_requests", foreign_keys=[borrower_id])  # Specifies the foreign key for the borrower relationship
    verify_by = db.relationship("AuthUser", back_populates="verify_requests", foreign_keys=[verifier_id])  # Specifies the foreign key for the verifier relationship

    def __init__(self, borrower_id, items , verifier_id, borrow_date, return_date):
        self.borrower_id = borrower_id
        if isinstance(items , list):
            self.items  = [db.session.query(Item).get(item_id) for item_id in items ]
        else:
            self.items  = [db.session.query(Item).get(items )]
        self.verifier_id = verifier_id
        self.borrow_date = borrow_date
        self.return_date = return_date

    def update(self, borrower_id, items , status, verifier_id, verify_status, borrow_date, return_date):
        self.borrower_id = borrower_id
        self.items  = items  if isinstance(items , list) else [items ]
        self.status = status
        self.verifier_id = verifier_id
        self.verify_status = verify_status
        self.borrow_date = borrow_date
        self.return_date = return_date

    def update_status(self, status):
        self.status = status

    def update_verify_status(self, verify_status):
        self.verify_status = verify_status
