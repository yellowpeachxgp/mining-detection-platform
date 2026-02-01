"""Flask 应用入口 — 注册蓝图、初始化数据库、静态文件服务"""
import os
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from models import db
from config import DATABASE_URI, SECRET_KEY, UPLOAD_DIR, JOB_DIR, MATLAB_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    CORS(app)

    # 数据库配置
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = SECRET_KEY

    # 初始化数据库
    db.init_app(app)

    # 确保目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(JOB_DIR, exist_ok=True)

    # 注册蓝图
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp
    from routes.job_routes import job_bp
    from routes.tile_routes import tile_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(tile_bp)
    app.register_blueprint(admin_bp)

    # 在首次请求前创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化默认管理员
        _ensure_admin()

    # ============= 静态文件服务 =============

    # React 构建输出目录
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    # 旧前端目录（备用）
    frontend_legacy = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend_legacy"))

    def get_frontend_dir():
        """优先使用 React 构建输出，否则使用旧前端"""
        if os.path.exists(os.path.join(frontend_dist, "index.html")):
            return frontend_dist
        return frontend_legacy

    @app.get("/")
    def home():
        return send_from_directory(get_frontend_dir(), "index.html")

    @app.get("/favicon.ico")
    def favicon_ico():
        fdir = get_frontend_dir()
        if os.path.exists(os.path.join(fdir, "favicon.svg")):
            return send_from_directory(fdir, "favicon.svg", mimetype="image/svg+xml")
        if os.path.exists(os.path.join(fdir, "favicon.ico")):
            return send_from_directory(fdir, "favicon.ico")
        return "", 204

    @app.get("/<path:path>")
    def frontend_static(path):
        """提供前端静态资源，支持 React Router 的 HTML5 History 模式"""
        # API 和 jobs 路径不走此路由
        if path.startswith("api/") or path.startswith("jobs/"):
            return jsonify({"error": "请求的资源不存在"}), 404

        fdir = get_frontend_dir()
        # 尝试返回静态文件
        full_path = os.path.join(fdir, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(fdir, path)

        # React Router: 其他路径返回 index.html
        return send_from_directory(fdir, "index.html")

    # ============= 错误处理 =============

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "请求的资源不存在"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"服务器错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500

    logger.info(f"UPLOAD_DIR: {UPLOAD_DIR}")
    logger.info(f"JOB_DIR: {JOB_DIR}")
    logger.info(f"MATLAB_DIR: {MATLAB_DIR}")
    logger.info(f"Frontend: {get_frontend_dir()}")

    return app


def _ensure_admin():
    """确保默认管理员账户存在"""
    from models import User
    from werkzeug.security import generate_password_hash
    from config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD

    admin = User.query.filter_by(username=DEFAULT_ADMIN_USERNAME).first()
    if admin is None:
        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=generate_password_hash(DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        logger.info(f"默认管理员已创建: {DEFAULT_ADMIN_USERNAME}")


app = create_app()

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("启动露天矿区检测平台")
    logger.info("访问地址: http://127.0.0.1:5001")
    logger.info("=" * 50)
    app.run(host="127.0.0.1", port=5001, debug=False)
