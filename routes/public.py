from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app

from extensions import db
from models import Room, Booking
from utils import filter_rooms, notify, log_visit

public_bp = Blueprint("public", __name__)


@public_bp.route("/uploads/profile_pics/<path:filename>")
def profile_pic(filename):
    return send_from_directory(current_app.config["PROFILE_PIC_FOLDER"], filename)


@public_bp.route("/uploads/rooms/<path:filename>")
def room_image(filename):
    return send_from_directory(current_app.config["ROOM_IMAGE_FOLDER"], filename)


@public_bp.before_app_request
def track_visitor():
    # Very lightweight visit counter - increments once per request to a page view.
    # Kept out of static/upload requests to avoid noise.
    if request.endpoint in ("public.home",):
        log_visit()


@public_bp.route("/")
def home():
    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

    approved_rooms = Room.query.filter_by(status="approved", is_available=True).order_by(
        Room.created_at.desc()
    ).all()

    rooms = filter_rooms(
        approved_rooms, query=query, location=location, min_price=min_price, max_price=max_price
    )

    featured_rooms = approved_rooms[:6]

    return render_template(
        "index.html",
        rooms=rooms,
        featured_rooms=featured_rooms,
        query=query,
        location=location,
        min_price=min_price,
        max_price=max_price,
    )


@public_bp.route("/room/<int:room_id>")
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status != "approved":
        flash("This room listing is not currently available.", "warning")
        return redirect(url_for("public.home"))
    return render_template("room_detail.html", room=room)


@public_bp.route("/room/<int:room_id>/book", methods=["POST"])
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status != "approved":
        flash("This room is not available for booking.", "danger")
        return redirect(url_for("public.home"))

    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    gender = request.form.get("gender", "").strip()
    caste = request.form.get("caste", "").strip()

    if not all([full_name, phone, email]):
        flash("Please fill in your name, phone, and email to book.", "danger")
        return redirect(url_for("public.room_detail", room_id=room.id))

    booking = Booking(
        room_id=room.id,
        full_name=full_name,
        phone=phone,
        email=email,
        gender=gender,
        caste=caste,
    )
    db.session.add(booking)
    db.session.commit()

    notify(
        f"New booking request for '{room.title}' from {full_name}",
        category="booking_request",
        recipient_role="owner",
        recipient_id=room.owner_id,
    )

    flash("Booking request submitted! The room owner has been notified.", "success")
    return redirect(url_for("public.room_detail", room_id=room.id))
