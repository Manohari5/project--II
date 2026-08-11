from datetime import datetime
from extensions import db


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(150), nullable=False)

    is_available = db.Column(db.Boolean, default=True)

    # Approval workflow - hidden from public until Admin approves
    status = db.Column(db.String(20), default="pending")  # 'pending', 'approved', 'rejected'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship("RoomImage", backref="room", lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="room", lazy=True, cascade="all, delete-orphan")

    @property
    def cover_image(self):
        if self.images:
            return self.images[0].filename
        return "default_room.png"

    def __repr__(self):
        return f"<Room {self.title}>"


class RoomImage(db.Model):
    __tablename__ = "room_images"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
