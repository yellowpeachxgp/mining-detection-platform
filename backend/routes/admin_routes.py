"""管理员路由蓝图"""
import os
import shutil
import logging
from flask import Blueprint, request, jsonify
from models import db, User, Job
from decorators import admin_required
from config import UPLOAD_DIR, JOB_DIR, DATA_DIR

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def get_dir_size(path):
    """递归计算目录大小"""
    total = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
    return total


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


@admin_bp.get("/stats")
@admin_required
def stats():
    """统计概览"""
    try:
        user_count = User.query.count()
        job_count = Job.query.count()
        completed_count = Job.query.filter_by(status="completed").count()
        failed_count = Job.query.filter_by(status="failed").count()

        upload_size = get_dir_size(UPLOAD_DIR)
        job_size = get_dir_size(JOB_DIR)

        return jsonify({
            "users": user_count,
            "jobs": {
                "total": job_count,
                "completed": completed_count,
                "failed": failed_count,
            },
            "disk": {
                "uploads": format_size(upload_size),
                "results": format_size(job_size),
                "total": format_size(upload_size + job_size),
            },
        })
    except Exception as e:
        logger.error(f"统计异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@admin_bp.get("/users")
@admin_required
def list_users():
    """用户列表"""
    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)

        query = User.query.order_by(User.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        users = []
        for u in pagination.items:
            d = u.to_dict()
            d["job_count"] = u.jobs.count()
            users.append(d)

        return jsonify({
            "users": users,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        })
    except Exception as e:
        logger.error(f"获取用户列表异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@admin_bp.put("/users/<int:user_id>")
@admin_required
def update_user(user_id):
    """修改用户"""
    try:
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "用户不存在"}), 404

        data = request.get_json(force=True)

        if "role" in data and data["role"] in ("user", "admin"):
            user.role = data["role"]
        if "is_active" in data:
            user.is_active = bool(data["is_active"])

        db.session.commit()
        logger.info(f"管理员修改用户: id={user_id}")
        return jsonify({"message": "更新成功", "user": user.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"修改用户异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@admin_bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    """删除用户"""
    try:
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "用户不存在"}), 404

        # 不允许删除自己
        from flask import g
        if user.id == g.user_id:
            return jsonify({"error": "不能删除自己的账户"}), 400

        # 删除用户关联的任务文件
        for job in user.jobs:
            upload_dir = os.path.join(UPLOAD_DIR, job.job_id)
            job_dir = os.path.join(JOB_DIR, job.job_id)
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir, ignore_errors=True)
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir, ignore_errors=True)

        db.session.delete(user)
        db.session.commit()
        logger.info(f"管理员删除用户: id={user_id}, username={user.username}")
        return jsonify({"message": "用户已删除"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@admin_bp.get("/jobs")
@admin_required
def list_all_jobs():
    """全部任务列表"""
    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 20)), 100)

        query = Job.query.order_by(Job.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        jobs = []
        for j in pagination.items:
            d = j.to_dict()
            d["username"] = j.user.username if j.user else "未知"
            jobs.append(d)

        return jsonify({
            "jobs": jobs,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        })
    except Exception as e:
        logger.error(f"获取全部任务列表异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@admin_bp.delete("/jobs/<job_id>")
@admin_required
def admin_delete_job(job_id):
    """管理员删除任何任务"""
    try:
        job = Job.query.filter_by(job_id=job_id).first()
        if job is None:
            return jsonify({"error": "任务不存在"}), 404

        upload_dir = os.path.join(UPLOAD_DIR, job_id)
        job_dir = os.path.join(JOB_DIR, job_id)
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir, ignore_errors=True)
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)

        db.session.delete(job)
        db.session.commit()

        logger.info(f"管理员删除任务: job_id={job_id}")
        return jsonify({"message": "任务已删除"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"管理员删除任务异常: {str(e)}")
        return jsonify({"error": str(e)}), 500
