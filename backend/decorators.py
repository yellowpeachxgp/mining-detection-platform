"""路由装饰器：JWT 认证和角色检查"""
from functools import wraps
from flask import request, jsonify, g
from auth import decode_token
from models import db, User


def jwt_required(f):
    """要求有效的 access_token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "缺少认证令牌"}), 401

        token = auth_header[7:]
        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "令牌无效或已过期"}), 401
        if payload.get("type") != "access":
            return jsonify({"error": "令牌类型错误"}), 401

        user = db.session.get(User, payload["user_id"])
        if user is None or not user.is_active:
            return jsonify({"error": "用户不存在或已禁用"}), 401

        g.user_id = user.id
        g.user_role = user.role
        g.user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """要求管理员角色（必须搭配 jwt_required 使用）"""
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if g.user_role != "admin":
            return jsonify({"error": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated
