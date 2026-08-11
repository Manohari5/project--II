from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from extensions import db
from models import User, Room, Booking, Notification, VisitorLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    total_users = User.query.filter_by(role="owner").count()
    total_owners = total_users
    total_rooms = Room.query.count()
    pending_owners = User.query.filter_by(role="owner", status="pending").count()
    pending_rooms = Room.query.filter_by(status="pending").count()
    approved_rooms = Room.query.filter_by(status="approved").count()
    rejected_rooms = Room.query.filter_by(status="rejected").count()
    total_visitors = db.session.query(db.func.sum(VisitorLog.count)).scalar() or 0

    stats = {
        "total_users": total_users,
        "total_owners": total_owners,
        "total_rooms": total_rooms,
        "pending_requests": pending_owners + pending_rooms,
        "approved_rooms": approved_rooms,
        "rejected_rooms": rejected_rooms,
        "total_visitors": total_visitors,
    }

    visitor_logs = VisitorLog.query.order_by(VisitorLog.visit_date.asc()).limit(14).all()
    chart_labels = [v.visit_date.strftime("%b %d") for v in visitor_logs]
    chart_data = [v.count for v in visitor_logs]

    recent_notifications = Notification.query.filter_by(recipient_role="admin").order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        chart_labels=chart_labels,
        chart_data=chart_data,
        recent_notifications=recent_notifications,
    )


@admin_bp.route("/owners")
@login_required
@admin_required
def owners():
    owner_list = User.query.filter_by(role="owner").order_by(User.created_at.desc()).all()
    return render_template("admin/owners.html", owners=owner_list)


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    # No separate "Room Seeker" accounts exist (booking is done without registration),
    # so this overview shows all registered accounts (Room Owners) for the admin.
    all_users = User.query.filter_by(role="owner").order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/owners/<int:user_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_owner(user_id):
    owner = User.query.filter_by(id=user_id, role="owner").first_or_404()
    owner.status = "approved"
    db.session.commit()
    flash(f"{owner.full_name}'s account has been approved.", "success")
    return redirect(url_for("admin.owners"))


@admin_bp.route("/owners/<int:user_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_owner(user_id):
    owner = User.query.filter_by(id=user_id, role="owner").first_or_404()
    owner.status = "rejected"
    db.session.commit()
    flash(f"{owner.full_name}'s account has been rejected.", "info")
    return redirect(url_for("admin.owners"))


@admin_bp.route("/owners/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_owner(user_id):
    owner = User.query.filter_by(id=user_id, role="owner").first_or_404()
    db.session.delete(owner)
    db.session.commit()
    flash("Room Owner account deleted.", "info")
    return redirect(url_for("admin.owners"))


@admin_bp.route("/rooms")
@login_required
@admin_required
def rooms():
    room_list = Room.query.order_by(Room.created_at.desc()).all()
    return render_template("admin/rooms.html", rooms=room_list)


@admin_bp.route("/rooms/<int:room_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_room(room_id):
    room = Room.query.get_or_404(room_id)
    room.status = "approved"
    db.session.commit()
    flash(f"Room '{room.title}' approved and now visible on the Home Page.", "success")
    return redirect(url_for("admin.pending"))


@admin_bp.route("/rooms/<int:room_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_room(room_id):
    room = Room.query.get_or_404(room_id)
    room.status = "rejected"
    db.session.commit()
    flash(f"Room '{room.title}' rejected.", "info")
    return redirect(url_for("admin.pending"))


@admin_bp.route("/rooms/<int:room_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    flash("Room listing deleted.", "info")
    return redirect(url_for("admin.rooms"))


@admin_bp.route("/pending")
@login_required
@admin_required
def pending():
    pending_owners = User.query.filter_by(role="owner", status="pending").all()
    pending_rooms = Room.query.filter_by(status="pending").all()
    return render_template("admin/pending.html", pending_owners=pending_owners, pending_rooms=pending_rooms)


@admin_bp.route("/notifications")
@login_required
@admin_required
def notifications():
    all_notes = Notification.query.filter_by(recipient_role="admin").order_by(
        Notification.created_at.desc()
    ).all()
    for note in all_notes:
        note.is_read = True
    db.session.commit()
    return render_template("admin/notifications.html", notifications=all_notes)


@admin_bp.route("/visitors")
@login_required
@admin_required
def visitors():
    logs = VisitorLog.query.order_by(VisitorLog.visit_date.asc()).all()
    labels = [v.visit_date.strftime("%b %d") for v in logs]
    data = [v.count for v in logs]
    total_users = User.query.filter_by(role="owner").count()
    total_rooms = Room.query.count()
    return render_template(
        "admin/visitors.html", labels=labels, data=data, total_users=total_users, total_rooms=total_rooms
    )


@admin_bp.route("/profile", methods=["GET", "POST"])
@login_required
@admin_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", current_user.full_name).strip()
        current_user.phone = request.form.get("phone", current_user.phone)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html")
