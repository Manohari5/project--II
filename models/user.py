from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """
    Single table used for both the Admin and Room Owner accounts.
    role: 'admin' or 'owner'
    Admin is created only via create_admin.py (never through the website).
    Room Owners must be approved by the Admin before they can log in.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, default="owner")  # 'admin' or 'owner'

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    phone = db.Column(db.String(20))
    location = db.Column(db.String(150))
    house_number = db.Column(db.String(50))
    profile_pic = db.Column(db.String(255), default="default.svg")

    # Approval workflow for Room Owners (Admin approves/rejects)
    status = db.Column(db.String(20), default="approved")  # 'pending', 'approved', 'rejected'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rooms = db.relationship("Room", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_owner(self):
        return self.role == "owner"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
