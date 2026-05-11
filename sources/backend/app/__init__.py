from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()

from app.config import Config
from app.extensions import db, jwt, socketio


def create_app(config_class=Config):
    import os
    dist_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dist")
    app = Flask(__name__, static_folder=dist_folder, static_url_path="")
    app.config.from_object(config_class)
    
    # 💡 告诉 Flask 信任前面的 1 层反向代理 (Nginx)
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    # 💡 核心并发优化：开启 SQLite WAL 模式并增加超时
    from sqlalchemy import event
    with app.app_context():
        if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite"):
            @event.listens_for(db.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=10000")  # 10秒超时等待
                cursor.close()

    @app.errorhandler(500)
    def handle_500(e):
        import traceback
        print("[Global Error Handler] 500 Internal Server Error:")
        traceback.print_exc()
        return {"error": "Internal Server Error", "message": str(e)}, 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e
            
        import traceback
        print("[Global Error Handler] Unhandled Exception:")
        traceback.print_exc()
        return {"error": str(e)}, 500

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
    from app.api.templates import bp as templates_bp

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
    app.register_blueprint(templates_bp, url_prefix="/api/templates")


    # 💡 增加：支持从持久化存储路径读取图片
    @app.route("/static/images/<path:filename>")
    def custom_static(filename):
        import os
        from flask import send_from_directory
        storage_base = os.environ.get("STORAGE_PATH", app.root_path)
        return send_from_directory(os.path.join(storage_base, "static", "images"), filename)

    from app.sockets import collab  # noqa: F401  registers handlers

    with app.app_context():
        # 💡 增加：检测并修复不匹配的数据库结构
        try:
            db.create_all()
            # 💡 Self-healing: Ensure is_starred column exists
            from sqlalchemy import text
            try:
                db.session.execute(text("SELECT is_starred FROM audit_logs LIMIT 1"))
            except Exception:
                db.session.rollback()
                try:
                    print("[Bootstrap] Adding missing is_starred column to audit_logs...")
                    db.session.execute(text("ALTER TABLE audit_logs ADD COLUMN is_starred BOOLEAN DEFAULT FALSE"))
                    db.session.commit()
                except Exception as e2:
                    db.session.rollback()
                    print(f"[Bootstrap] Failed to auto-patch schema: {e2}")
        except Exception as e:
            print(f"❌ [Bootstrap] 数据库表创建失败! 请确保数据库已存在。 Error: {e}")
            if "Unknown database" in str(e):
                print("💡 提示：请先在 MySQL 中手动创建名为 'edms_db' 的空数据库。")
        
        # 💡 自动引导超级管理员账号
        def _bootstrap_admin():
            from app.models import User
            try:
                admin = User.query.filter_by(login_name='admin').first()
                if not admin:
                    # 如果没有任何部门，先尝试创建一个默认部门供 admin 使用
                    from app.models import Department
                    dept = Department.query.first()
                    if not dept:
                        dept = Department(code="EXEC", name="Executive Office")
                        db.session.add(dept)
                        db.session.flush()

                    admin = User(
                        login_name='admin',
                        employee_no='ADMIN001',
                        first_name='System',
                        last_name='Admin',
                        department_id=dept.id if dept else None,
                        is_manager=True,
                        registration_status='active'
                    )
                    admin.set_password('123456')
                    db.session.add(admin)
                    db.session.commit()
                    print("[Bootstrap] Admin user created.")
                else:
                    # 确保已有 admin 账户拥有管理权限和激活状态
                    needs_update = False
                    if not admin.is_manager:
                        admin.is_manager = True
                        needs_update = True
                    if admin.registration_status != 'active':
                        admin.registration_status = 'active'
                        needs_update = True
                    
                    if needs_update:
                        db.session.commit()
                        print("[Bootstrap] Admin permissions restored.")
            except Exception as e:
                db.session.rollback()
                print(f"[Bootstrap] Error creating/checking admin: {e}")

        _bootstrap_admin()

    # 💡 增加：捕捉所有非 API 路由并返回前端 index.html (支持 SPA)
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        import os
        from flask import send_from_directory
        if path.startswith("api/") or path.startswith("static/"):
             return {"error": "Not Found"}, 404
             
        # 检查文件是否存在
        file_path = os.path.join(app.static_folder, path)
        if path != "" and os.path.exists(file_path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, "index.html")

    return app
