from datetime import datetime
from extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    # recipient_role: 'admin' or 'owner'; recipient_id is only set for owner notifications
    recipient_role = db.Column(db.String(20), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), default="general")  # owner_registered, room_uploaded, booking_request
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.category}: {self.message}>"
