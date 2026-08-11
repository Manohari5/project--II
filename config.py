import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # NOTE: change this before deploying to production
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database", "room_rental.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    PROFILE_PIC_FOLDER = os.path.join(UPLOAD_FOLDER, "profile_pics")
    ROOM_IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, "rooms")

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB upload limit
