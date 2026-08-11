from datetime import datetime
from extensions import db


class Booking(db.Model):
    """
    A booking request submitted by a visitor (no account required).
    The booker's details are captured directly on the booking record.
    """
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)

    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(20))
    caste = db.Column(db.String(80))

    status = db.Column(db.String(20), default="pending")  # 'pending', 'accepted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Booking {self.full_name} -> room {self.room_id}>"
