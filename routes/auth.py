from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User
from utils import is_valid_gmail, save_upload, notify

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Room Owner self-registration. Admin is NEVER created here."""
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        house_number = request.form.get("house_number", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # --- Validation ---
        if not all([full_name, email, phone, location, username, password]):
            flash("Please fill in all required fields.", "danger")
            return render_template("register.html")

        if not is_valid_gmail(email):
            flash("Please use a valid Gmail address (e.g. name@gmail.com).", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("This username is already taken.", "danger")
            return render_template("register.html")

        profile_pic_file = request.files.get("profile_pic")
        profile_pic_name = save_upload(
            profile_pic_file, current_app.config["PROFILE_PIC_FOLDER"], prefix="owner_"
        ) or "default.svg"

        new_owner = User(
            role="owner",
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            house_number=house_number,
            username=username,
            profile_pic=profile_pic_name,
            status="approved",  # owner account itself is usable immediately per spec;
                                  # their ROOM LISTINGS still require admin approval.
        )
        new_owner.set_password(password)
        db.session.add(new_owner)
        db.session.commit()

        notify(
            f"New Room Owner registered: {new_owner.full_name} ({new_owner.username})",
            category="owner_registered",
            recipient_role="admin",
        )

        # Room Owners are automatically logged in on first registration
        login_user(new_owner)
        flash("Registration successful! Welcome to your dashboard.", "success")
        return redirect(url_for("owner.dashboard"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Shared login page for both Admin and Room Owner accounts."""
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("login.html")

        if user.is_owner and user.status == "rejected":
            flash("Your account has been rejected by the administrator.", "danger")
            return render_template("login.html")

        login_user(user)
        flash(f"Welcome back, {user.full_name}!", "success")

        if user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("owner.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))
