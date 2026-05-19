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

    # 💡 增加：统一的系统功能调用美化日志中间件
    def get_feature_description(method: str, path: str) -> str:
        if path.startswith("/api/auth/login"):
            return "用户登录 (User Login)"
        if path.startswith("/api/auth/register"):
            return "用户注册 (User Registration)"
        if path.startswith("/api/auth/me"):
            return "获取当前用户信息 (Get Profile)"
        if path.startswith("/api/auth/logout"):
            return "用户登出 (User Logout)"
            
        if path.startswith("/api/documents"):
            if method == "GET":
                if "tree" in path:
                    return "查看文档目录树结构 (Get Document Directory Tree)"
                if "diff" in path:
                    return "获取文档版本差异对比 (Get Version Diff)"
                return "获取文档列表 (List Documents)"
            if method == "POST":
                if "batch-move" in path:
                    return "批量移动文档空间 (Batch Move Documents)"
                return "创建新文档 (Create Document)"
            if method in ("PUT", "PATCH"):
                return "编辑文档元数据/内容 (Edit Document)"
            if method == "DELETE":
                return "删除文档 (Delete Document)"
                
        if path.startswith("/api/spaces"):
            if method == "GET":
                return "获取知识空间列表 (List Knowledge Spaces)"
            if method == "POST":
                return "创建新知识空间 (Create Knowledge Space)"
                
        if path.startswith("/api/comments"):
            return "发表/查看文档评论 (Comment Action)"
            
        if path.startswith("/api/approvals"):
            if method == "POST":
                return "提交/处理审批流程 (Submit/Process Approval)"
            return "查看审批流列表 (List Approvals)"
            
        if path.startswith("/api/ai"):
            if "ocr" in path:
                return "AI 图生文 / OCR 识别 (AI OCR Translation)"
            return "AI 智能写作/对话助手 (AI Writing/Chat Assistant)"
            
        if path.startswith("/api/master-data"):
            if "import" in path:
                return "主数据批量导入 (Import Master Data)"
            return "管理组织架构主数据 (Manage Master Data)"
            
        if path.startswith("/api/notifications"):
            return "获取通知消息列表 (List Notifications)"
            
        if path.startswith("/api/dashboard"):
            return "查看控制面板统计看板 (Get Dashboard Analytics)"
            
        if path.startswith("/api/users"):
            if "departments" in path:
                return "获取系统部门结构 (Get System Departments)"
            return "管理/查询系统用户 (Manage Users)"
            
        return "其它系统操作 (Other Operation)"

    @app.before_request
    def log_request_start():
        import time
        from flask import g
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        g.start_time = time.time()
        user_info = "访客 (Guest / Unauthenticated)"
        
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                from app.models import User
                user = db.session.get(User, int(user_id))
                if user:
                    dept_name = user.department.name if user.department else "无部门 (No Dept)"
                    user_info = f"{user.login_name} (ID: {user.id} | {user.display_name()} | 部门: {dept_name})"
                else:
                    user_info = f"UserID: {user_id} (未在DB中找到该用户)"
        except Exception:
            pass
            
        g.user_info = user_info

    @app.after_request
    def log_request_end(response):
        import time
        from flask import request, g
        
        # 忽略静态资源、健康检查等以保持终端清洁
        ignored_prefixes = ("/static", "/favicon.ico", "/api/health")
        if request.path.startswith(ignored_prefixes):
            return response

        duration = 0.0
        if hasattr(g, "start_time"):
            duration = (time.time() - g.start_time) * 1000  # ms
            
        user_info = getattr(g, "user_info", "Guest")
        status = response.status_code
        
        # 根据状态码配置粗体色
        if status >= 500:
            status_color = "\033[1;31m"  # Bold Red
        elif status >= 400:
            status_color = "\033[1;33m"  # Bold Yellow
        elif status >= 300:
            status_color = "\033[1;34m"  # Bold Blue
        else:
            status_color = "\033[1;32m"  # Bold Green
            
        reset_color = "\033[0m"
        cyan_color = "\033[1;36m"
        purple_color = "\033[1;35m"
        gray_color = "\033[90m"
        
        feature_desc = get_feature_description(request.method, request.path)
        
        # 优雅的终端输出结构
        print(f"\n{gray_color}[{time.strftime('%Y-%m-%d %H:%M:%S')}]{reset_color} "
              f"{purple_color}[SYSTEM API LOG]{reset_color} "
              f"👤 操作人: {cyan_color}{user_info}{reset_color}\n"
              f"   🚀 请求: {request.method} {request.path}"
              f"{' ?' + request.query_string.decode('utf-8') if request.query_string else ''}\n"
              f"   ⚙️  功能: {purple_color}{feature_desc}{reset_color}\n"
              f"   ⏱️  耗时: {duration:.2f}ms | 状态: {status_color}{status}{reset_color}\n"
              f"{gray_color}" + "-" * 75 + f"{reset_color}")
              
        return response


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

            # 💡 Self-healing: Ensure is_super_admin column exists
            try:
                db.session.execute(text("SELECT is_super_admin FROM users LIMIT 1"))
            except Exception:
                db.session.rollback()
                try:
                    print("[Bootstrap] Adding missing is_super_admin column to users...")
                    db.session.execute(text("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE"))
                    db.session.commit()
                except Exception as e2:
                    db.session.rollback()
                    print(f"[Bootstrap] Failed to auto-patch users schema: {e2}")

            # 💡 Self-healing: Ensure doc_number column exists
            try:
                db.session.execute(text("SELECT doc_number FROM documents LIMIT 1"))
            except Exception:
                db.session.rollback()
                try:
                    print("[Bootstrap] Adding missing doc_number column to documents...")
                    db.session.execute(text("ALTER TABLE documents ADD COLUMN doc_number VARCHAR(64) UNIQUE NULL"))
                    db.session.commit()
                except Exception as e3:
                    db.session.rollback()
                    print(f"[Bootstrap] Failed to auto-patch documents schema: {e3}")
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
                        is_super_admin=True,
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
                    if not admin.is_super_admin:
                        admin.is_super_admin = True
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
