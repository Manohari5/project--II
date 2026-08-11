from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from extensions import db
from models import Room, RoomImage, Booking, Notification
from utils import save_upload, notify

owner_bp = Blueprint("owner", __name__, url_prefix="/owner")


def owner_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_owner:
            flash("Room Owner access required.", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


@owner_bp.route("/dashboard")
@login_required
@owner_required
def dashboard():
    my_rooms = Room.query.filter_by(owner_id=current_user.id).order_by(Room.created_at.desc()).all()
    total_rooms = len(my_rooms)
    approved = sum(1 for r in my_rooms if r.status == "approved")
    pending = sum(1 for r in my_rooms if r.status == "pending")

    room_ids = [r.id for r in my_rooms]
    pending_bookings = (
        Booking.query.filter(Booking.room_id.in_(room_ids), Booking.status == "pending").all()
        if room_ids else []
    )
    accepted_bookings = (
        Booking.query.filter(Booking.room_id.in_(room_ids), Booking.status == "accepted").all()
        if room_ids else []
    )

    return render_template(
        "owner/dashboard.html",
        my_rooms=my_rooms,
        total_rooms=total_rooms,
        approved=approved,
        pending=pending,
        pending_bookings=pending_bookings,
        accepted_bookings=accepted_bookings,
    )


@owner_bp.route("/profile", methods=["GET", "POST"])
@login_required
@owner_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip() or current_user.full_name
        current_user.phone = request.form.get("phone", "").strip() or current_user.phone
        current_user.location = request.form.get("location", "").strip() or current_user.location
        current_user.house_number = request.form.get("house_number", "").strip() or current_user.house_number
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("owner.profile"))

    return render_template("owner/profile.html")


@owner_bp.route("/profile/picture", methods=["POST"])
@login_required
@owner_required
def update_profile_picture():
    """Handles upload / update via the '+' icon on the circular profile picture."""
    file = request.files.get("profile_pic")
    filename = save_upload(file, current_app.config["PROFILE_PIC_FOLDER"], prefix="owner_")
    if filename:
        current_user.profile_pic = filename
        db.session.commit()
        flash("Profile picture updated.", "success")
    else:
        flash("Please choose a valid image file (png, jpg, jpeg, gif, webp).", "danger")
    return redirect(url_for("owner.profile"))


@owner_bp.route("/profile/picture/delete", methods=["POST"])
@login_required
@owner_required
def delete_profile_picture():
    current_user.profile_pic = "default.svg"
    db.session.commit()
    flash("Profile picture removed.", "info")
    return redirect(url_for("owner.profile"))


@owner_bp.route("/rooms")
@login_required
@owner_required
def rooms():
    my_rooms = Room.query.filter_by(owner_id=current_user.id).order_by(Room.created_at.desc()).all()
    return render_template("owner/rooms.html", rooms=my_rooms)


@owner_bp.route("/rooms/add", methods=["GET", "POST"])
@login_required
@owner_required
def add_room():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        location = request.form.get("location", "").strip()

        if not all([title, description, price, location]):
            flash("Please fill in all room details.", "danger")
            return render_template("owner/add_room.html")

        room = Room(
            owner_id=current_user.id,
            title=title,
            description=description,
            price=price,
            location=location,
            status="pending",  # hidden from public until admin approves
        )
        db.session.add(room)
        db.session.flush()  # get room.id before commit

        files = request.files.getlist("images")
        for f in files:
            filename = save_upload(f, current_app.config["ROOM_IMAGE_FOLDER"], prefix="room_")
            if filename:
                db.session.add(RoomImage(room_id=room.id, filename=filename))

        db.session.commit()

        notify(
            f"New room submitted for approval: '{room.title}' by {current_user.full_name}",
            category="room_uploaded",
            recipient_role="admin",
        )

        flash("Room submitted! It will appear publicly once approved by the admin.", "success")
        return redirect(url_for("owner.rooms"))

    return render_template("owner/add_room.html")


@owner_bp.route("/rooms/<int:room_id>/edit", methods=["GET", "POST"])
@login_required
@owner_required
def edit_room(room_id):
    room = Room.query.filter_by(id=room_id, owner_id=current_user.id).first_or_404()

    if request.method == "POST":
        room.title = request.form.get("title", room.title).strip()
        room.description = request.form.get("description", room.description).strip()
        room.price = request.form.get("price", type=float) or room.price
        room.location = request.form.get("location", room.location).strip()
        room.is_available = request.form.get("is_available") == "on"

        files = request.files.getlist("images")
        for f in files:
            filename = save_upload(f, current_app.config["ROOM_IMAGE_FOLDER"], prefix="room_")
            if filename:
                db.session.add(RoomImage(room_id=room.id, filename=filename))

        db.session.commit()
        flash("Room updated successfully.", "success")
        return redirect(url_for("owner.rooms"))

    return render_template("owner/edit_room.html", room=room)


@owner_bp.route("/rooms/<int:room_id>/delete", methods=["POST"])
@login_required
@owner_required
def delete_room(room_id):
    room = Room.query.filter_by(id=room_id, owner_id=current_user.id).first_or_404()
    db.session.delete(room)
    db.session.commit()
    flash("Room listing deleted.", "info")
    return redirect(url_for("owner.rooms"))


@owner_bp.route("/rooms/image/<int:image_id>/delete", methods=["POST"])
@login_required
@owner_required
def delete_room_image(image_id):
    image = RoomImage.query.get_or_404(image_id)
    room = Room.query.filter_by(id=image.room_id, owner_id=current_user.id).first_or_404()
    db.session.delete(image)
    db.session.commit()
    flash("Image removed.", "info")
    return redirect(url_for("owner.edit_room", room_id=room.id))


@owner_bp.route("/bookings")
@login_required
@owner_required
def bookings():
    room_ids = [r.id for r in Room.query.filter_by(owner_id=current_user.id).all()]
    pending_bookings = (
        Booking.query.filter(Booking.room_id.in_(room_ids), Booking.status == "pending")
        .order_by(Booking.created_at.desc()).all() if room_ids else []
    )
    accepted_bookings = (
        Booking.query.filter(Booking.room_id.in_(room_ids), Booking.status == "accepted")
        .order_by(Booking.created_at.desc()).all() if room_ids else []
    )
    return render_template("owner/bookings.html", pending_bookings=pending_bookings, accepted_bookings=accepted_bookings)


@owner_bp.route("/bookings/<int:booking_id>/accept", methods=["POST"])
@login_required
@owner_required
def accept_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    room = Room.query.filter_by(id=booking.room_id, owner_id=current_user.id).first_or_404()
    booking.status = "accepted"
    db.session.commit()
    flash(f"Booking from {booking.full_name} accepted.", "success")
    return redirect(url_for("owner.bookings"))


@owner_bp.route("/bookings/<int:booking_id>/delete", methods=["POST"])
@login_required
@owner_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    room = Room.query.filter_by(id=booking.room_id, owner_id=current_user.id).first_or_404()
    db.session.delete(booking)
    db.session.commit()
    flash("Booking request deleted.", "info")
    return redirect(url_for("owner.bookings"))


@owner_bp.route("/notifications")
@login_required
@owner_required
def notifications():
    all_notes = Notification.query.filter_by(
        recipient_role="owner", recipient_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    for note in all_notes:
        note.is_read = True
    db.session.commit()
    return render_template("owner/notifications.html", notifications=all_notes)
