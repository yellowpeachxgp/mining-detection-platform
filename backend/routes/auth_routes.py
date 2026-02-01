"""认证路由蓝图"""
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from auth import generate_access_token, generate_refresh_token, decode_token

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    """用户注册"""
    try:
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not username or not email or not password:
            return jsonify({"error": "用户名、邮箱和密码均为必填"}), 400
        if len(username) < 2 or len(username) > 80:
            return jsonify({"error": "用户名长度应为 2-80 个字符"}), 400
        if len(password) < 6:
            return jsonify({"error": "密码至少 6 个字符"}), 400
        if "@" not in email:
            return jsonify({"error": "邮箱格式无效"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "用户名已存在"}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "邮箱已被注册"}), 409

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role="user",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        logger.info(f"新用户注册: {username}")
        return jsonify({"message": "注册成功", "user": user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"注册异常: {str(e)}")
        return jsonify({"error": f"注册失败: {str(e)}"}), 500


@auth_bp.post("/login")
def login():
    """用户登录"""
    try:
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "用户名和密码均为必填"}), 400

        user = User.query.filter_by(username=username).first()
        if user is None or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "用户名或密码错误"}), 401
        if not user.is_active:
            return jsonify({"error": "账户已被禁用，请联系管理员"}), 403

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        access_token = generate_access_token(user.id, user.role)
        refresh_token = generate_refresh_token(user.id)

        logger.info(f"用户登录: {username}")
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        })
    except Exception as e:
        logger.error(f"登录异常: {str(e)}")
        return jsonify({"error": f"登录失败: {str(e)}"}), 500


@auth_bp.post("/refresh")
def refresh():
    """刷新 access_token"""
    try:
        data = request.get_json(force=True)
        refresh_token = data.get("refresh_token", "")

        if not refresh_token:
            return jsonify({"error": "缺少 refresh_token"}), 400

        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return jsonify({"error": "refresh_token 无效或已过期"}), 401

        user = db.session.get(User, payload["user_id"])
        if user is None or not user.is_active:
            return jsonify({"error": "用户不存在或已禁用"}), 401

        access_token = generate_access_token(user.id, user.role)
        return jsonify({
            "access_token": access_token,
            "user": user.to_dict(),
        })
    except Exception as e:
        logger.error(f"刷新令牌异常: {str(e)}")
        return jsonify({"error": f"刷新失败: {str(e)}"}), 500
