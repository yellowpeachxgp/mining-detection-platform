"""用户路由蓝图"""
import logging
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from models import db
from decorators import jwt_required

logger = logging.getLogger(__name__)
user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.get("/profile")
@jwt_required
def get_profile():
    """获取当前用户信息"""
    return jsonify(g.user.to_dict())


@user_bp.put("/profile")
@jwt_required
def update_profile():
    """更新个人信息"""
    try:
        data = request.get_json(force=True)
        email = data.get("email", "").strip()

        if email:
            if "@" not in email:
                return jsonify({"error": "邮箱格式无效"}), 400
            from models import User
            existing = User.query.filter(User.email == email, User.id != g.user_id).first()
            if existing:
                return jsonify({"error": "邮箱已被其他用户使用"}), 409
            g.user.email = email

        db.session.commit()
        return jsonify({"message": "更新成功", "user": g.user.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新个人信息异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@user_bp.put("/password")
@jwt_required
def change_password():
    """修改密码"""
    try:
        data = request.get_json(force=True)
        old_password = data.get("old_password", "")
        new_password = data.get("new_password", "")

        if not old_password or not new_password:
            return jsonify({"error": "旧密码和新密码均为必填"}), 400
        if len(new_password) < 6:
            return jsonify({"error": "新密码至少 6 个字符"}), 400

        if not check_password_hash(g.user.password_hash, old_password):
            return jsonify({"error": "旧密码错误"}), 401

        g.user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        logger.info(f"用户修改密码: {g.user.username}")
        return jsonify({"message": "密码修改成功"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"修改密码异常: {str(e)}")
        return jsonify({"error": str(e)}), 500
