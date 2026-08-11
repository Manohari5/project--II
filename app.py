import os
from flask import Flask
from flask_login import current_user

from config import Config, BASE_DIR
from extensions import db, login_manager
from models import User, Notification


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure required folders exist
    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
    os.makedirs(app.config["PROFILE_PIC_FOLDER"], exist_ok=True)
    os.makedirs(app.config["ROOM_IMAGE_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.public import public_bp
    from routes.admin import admin_bp
    from routes.owner import owner_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(owner_bp)

    # Make notification badge counts available in every template (for base.html)
    @app.context_processor
    def inject_notification_counts():
        if current_user.is_authenticated:
            if current_user.is_admin:
                count = Notification.query.filter_by(recipient_role="admin", is_read=False).count()
            else:
                count = Notification.query.filter_by(
                    recipient_role="owner", recipient_id=current_user.id, is_read=False
                ).count()
        else:
            count = 0
        return {"unread_notifications": count}

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
