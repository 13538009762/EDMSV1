"""EDMS Flask application factory."""
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, jwt, socketio


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    # 💡 增加：健康检查接口 (放在最前面确保不被拦截)
    @app.route("/api/health")
    def health_check():
        return {"status": "ok"}

    from app.api.auth import bp as auth_bp
    from app.api.master_data import bp as master_bp
    from app.api.documents import bp as documents_bp
    from app.api.comments import bp as comments_bp
    from app.api.approvals import bp as approvals_bp
    from app.api.users import bp as users_bp
    from app.api.admin import bp as admin_bp
    from app.api.dashboard import bp as dashboard_bp
    from app.api.ai import bp as ai_bp
    from app.api.spaces import bp as spaces_bp
    from app.api.notifications import bp as notifications_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(master_bp, url_prefix="/api/master-data")
    app.register_blueprint(documents_bp, url_prefix="/api/documents")
    app.register_blueprint(comments_bp, url_prefix="/api")
    app.register_blueprint(approvals_bp, url_prefix="/api/approvals")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(spaces_bp, url_prefix="/api/spaces")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")


    # 💡 增加：支持从持久化存储路径读取图片
    @app.route("/static/images/<path:filename>")
    def custom_static(filename):
        import os
        from flask import send_from_directory
        storage_base = os.environ.get("STORAGE_PATH", app.root_path)
        return send_from_directory(os.path.join(storage_base, "static", "images"), filename)

    from app.sockets import collab  # noqa: F401  registers handlers

    with app.app_context():
        db.create_all()

    return app
