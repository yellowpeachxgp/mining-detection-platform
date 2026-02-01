"""数据库初始化脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User
from config import (
    DATABASE_URI, DATA_DIR, UPLOAD_DIR, JOB_DIR,
    DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
)


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def init_database():
    """初始化数据库：创建表和默认管理员"""
    app = create_app()

    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(JOB_DIR, exist_ok=True)

    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表已创建")

        # 检查是否已有管理员
        admin = User.query.filter_by(username=DEFAULT_ADMIN_USERNAME).first()
        if admin is None:
            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                password_hash=generate_password_hash(DEFAULT_ADMIN_PASSWORD),
                role="admin",
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✓ 默认管理员已创建: {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}")
            print("  ⚠️ 请在首次登录后修改默认密码!")
        else:
            print(f"✓ 管理员账户已存在: {DEFAULT_ADMIN_USERNAME}")

        # 显示数据库信息
        user_count = User.query.count()
        print(f"✓ 当前用户数: {user_count}")
        print(f"✓ 数据库位置: {DATABASE_URI}")


if __name__ == "__main__":
    init_database()
