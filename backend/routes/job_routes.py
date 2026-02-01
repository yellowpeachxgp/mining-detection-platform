"""检测任务路由蓝图 — 迁移自 app.py 并添加认证和数据库"""
import os
import io
import uuid
import json
import logging
import zipfile
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_from_directory, send_file, g
from models import db, Job, JobFile
from decorators import jwt_required
from config import UPLOAD_DIR, JOB_DIR
from runners import get_runner
from services.geo_service import (
    get_crs_info, get_geotiff_bounds, sample_timeseries,
    sample_singleband, format_file_size,
)

logger = logging.getLogger(__name__)
job_bp = Blueprint("job", __name__)

# 预定义输出文件信息
OUTPUT_FILES = [
    ("mining_disturbance_mask.tif", "扰动掩膜"),
    ("mining_disturbance_year.tif", "扰动年份"),
    ("mining_recovery_year.tif", "恢复年份"),
    ("potential_disturbance.tif", "潜在扰动"),
    ("res_disturbance_type.tif", "扰动类型"),
    ("year_disturbance_raw.tif", "原始扰动年份"),
    ("year_recovery_raw.tif", "原始恢复年份"),
]


@job_bp.post("/api/upload")
@jwt_required
def upload():
    """上传 GeoTIFF 文件"""
    try:
        f = request.files.get("file")
        kind = request.form.get("kind")
        job_id = request.form.get("job_id") or str(uuid.uuid4())

        if f is None or kind not in ("ndvi", "coal"):
            return jsonify({"error": "需要 file 和 kind(ndvi|coal)"}), 400

        job_upload_dir = os.path.join(UPLOAD_DIR, job_id)
        os.makedirs(job_upload_dir, exist_ok=True)

        filename = f"{kind}.tif"
        path = os.path.join(job_upload_dir, filename)
        f.save(path)

        # 确保数据库中有 Job 记录
        job = Job.query.filter_by(job_id=job_id).first()
        if job is None:
            job = Job(job_id=job_id, user_id=g.user_id, status="pending")
            db.session.add(job)

        # 记录原始文件名
        original_name = f.filename or filename
        if kind == "ndvi":
            job.ndvi_filename = original_name
        else:
            job.coal_filename = original_name

        db.session.commit()

        logger.info(f"上传成功: job_id={job_id}, kind={kind}")
        return jsonify({"job_id": job_id, "kind": kind, "path": path})
    except Exception as e:
        db.session.rollback()
        logger.error(f"上传异常: {str(e)}")
        return jsonify({"error": f"上传失败: {str(e)}"}), 500


@job_bp.post("/api/run")
@jwt_required
def run_job():
    """执行检测"""
    try:
        data = request.get_json(force=True)
        job_id = data.get("job_id")
        startyear = int(data.get("startyear", 2010))
        engine = data.get("engine")

        if not job_id:
            return jsonify({"error": "缺少 job_id"}), 400

        ndvi_path = os.path.join(UPLOAD_DIR, job_id, "ndvi.tif")
        coal_path = os.path.join(UPLOAD_DIR, job_id, "coal.tif")

        if not os.path.exists(ndvi_path):
            return jsonify({"error": "缺少 ndvi.tif"}), 400
        if not os.path.exists(coal_path):
            return jsonify({"error": "缺少 coal.tif"}), 400

        out_dir = os.path.join(JOB_DIR, job_id)
        os.makedirs(out_dir, exist_ok=True)

        # 更新 Job 状态
        job = Job.query.filter_by(job_id=job_id).first()
        if job is None:
            job = Job(job_id=job_id, user_id=g.user_id, status="running")
            db.session.add(job)
        else:
            job.status = "running"

        job.startyear = startyear
        db.session.commit()

        try:
            runner = get_runner(engine)
            engine_name = type(runner).__name__
            job.engine = engine_name
            logger.info(f"开始检测: job_id={job_id}, startyear={startyear}, engine={engine_name}")

            result = runner.run_detect(ndvi_path, coal_path, out_dir, startyear)
            logger.info(f"检测完成: job_id={job_id}, engine={engine_name}")

            # 更新 Job 完成状态
            bounds = get_geotiff_bounds(ndvi_path)
            crs_info = get_crs_info(ndvi_path)

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.bounds = bounds
            job.crs_info = crs_info

            # 记录输出文件
            JobFile.query.filter_by(job_db_id=job.id, file_type="output").delete()
            for filename, label in OUTPUT_FILES:
                fpath = os.path.join(out_dir, filename)
                if os.path.exists(fpath):
                    jf = JobFile(
                        job_db_id=job.id,
                        filename=filename,
                        label=label,
                        file_type="output",
                        size=os.path.getsize(fpath),
                    )
                    db.session.add(jf)

            db.session.commit()

        except Exception as run_err:
            job.status = "failed"
            job.error_message = str(run_err)
            db.session.commit()
            raise

        def url_for(name):
            return f"/jobs/{job_id}/{name}"

        return jsonify({
            "job_id": job_id,
            "bounds": bounds,
            "crs_info": crs_info,
            "outputs": {
                "mining_disturbance_mask": url_for("mining_disturbance_mask.tif"),
                "mining_disturbance_year": url_for("mining_disturbance_year.tif"),
                "mining_recovery_year": url_for("mining_recovery_year.tif"),
                "potential_disturbance": url_for("potential_disturbance.tif"),
                "res_disturbance_type": url_for("res_disturbance_type.tif"),
                "year_disturbance_raw": url_for("year_disturbance_raw.tif"),
                "year_recovery_raw": url_for("year_recovery_raw.tif"),
            },
        })
    except Exception as e:
        logger.error(f"检测异常: {str(e)}")
        return jsonify({"error": f"检测失败: {str(e)}"}), 500


@job_bp.get("/api/ndvi-timeseries")
@jwt_required
def ndvi_timeseries():
    """查询 NDVI 时间序列"""
    try:
        job_id = request.args.get("job_id")
        lon = float(request.args.get("lon"))
        lat = float(request.args.get("lat"))
        startyear = int(request.args.get("startyear", 2010))

        if not job_id:
            return jsonify({"error": "缺少 job_id"}), 400

        ndvi_path = os.path.join(UPLOAD_DIR, job_id, "ndvi.tif")
        dist_year_path = os.path.join(JOB_DIR, job_id, "mining_disturbance_year.tif")
        recv_year_path = os.path.join(JOB_DIR, job_id, "mining_recovery_year.tif")

        if not os.path.exists(ndvi_path):
            return jsonify({"error": "NDVI文件不存在"}), 404

        vals, band_count = sample_timeseries(ndvi_path, lon, lat)
        years = list(range(startyear, startyear + band_count))

        disturbance_year = None
        recovery_year = None

        if os.path.exists(dist_year_path):
            disturbance_year = sample_singleband(dist_year_path, lon, lat)
        if os.path.exists(recv_year_path):
            recovery_year = sample_singleband(recv_year_path, lon, lat)

        logger.info(f"查询成功: job_id={job_id}, lon={lon}, lat={lat}")
        return jsonify({
            "job_id": job_id,
            "lon": lon,
            "lat": lat,
            "years": years,
            "ndvi": vals,
            "disturbance_year": disturbance_year,
            "recovery_year": recovery_year,
        })
    except Exception as e:
        logger.error(f"查询异常: {str(e)}")
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@job_bp.get("/api/job-files/<job_id>")
@jwt_required
def list_job_files(job_id):
    """列出任务的所有输出文件"""
    try:
        job_dir = os.path.join(JOB_DIR, job_id)
        if not os.path.exists(job_dir):
            return jsonify({"error": "任务不存在"}), 404

        files = []
        for filename, label in OUTPUT_FILES:
            path = os.path.join(job_dir, filename)
            if os.path.exists(path):
                size = os.path.getsize(path)
                files.append({
                    "filename": filename,
                    "label": label,
                    "size": size,
                    "size_formatted": format_file_size(size),
                    "url": f"/jobs/{job_id}/{filename}",
                })

        return jsonify({"job_id": job_id, "files": files})
    except Exception as e:
        logger.error(f"列出文件错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@job_bp.post("/api/download-zip/<job_id>")
@jwt_required
def download_zip(job_id):
    """打包下载选中的文件"""
    try:
        data = request.get_json(force=True)
        filenames = data.get("filenames", [])

        if not filenames:
            return jsonify({"error": "未选择任何文件"}), 400

        job_dir = os.path.join(JOB_DIR, job_id)
        if not os.path.exists(job_dir):
            return jsonify({"error": "任务不存在"}), 404

        valid_files = []
        for filename in filenames:
            if ".." in filename or "/" in filename or "\\" in filename:
                continue
            path = os.path.join(job_dir, filename)
            if os.path.exists(path):
                valid_files.append((filename, path))

        if not valid_files:
            return jsonify({"error": "没有有效的文件"}), 400

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, path in valid_files:
                zf.write(path, filename)

        zip_buffer.seek(0)

        logger.info(f"打包下载: job_id={job_id}, 文件数={len(valid_files)}")
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"mining_results_{job_id[:8]}.zip",
        )
    except Exception as e:
        logger.error(f"打包下载错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@job_bp.get("/jobs/<job_id>/<filename>")
def serve_job_file(job_id, filename):
    """提供结果文件（无需认证，以便地图图层加载）"""
    try:
        d = os.path.join(JOB_DIR, job_id)
        return send_from_directory(d, filename, as_attachment=False)
    except Exception as e:
        logger.error(f"获取文件异常: {str(e)}")
        return jsonify({"error": f"文件不存在: {str(e)}"}), 404


# ============= 历史记录 API =============

@job_bp.get("/api/jobs")
@jwt_required
def list_jobs():
    """获取当前用户的任务列表"""
    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 10)), 50)

        query = Job.query.filter_by(user_id=g.user_id).order_by(Job.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "jobs": [j.to_dict() for j in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        })
    except Exception as e:
        logger.error(f"获取任务列表异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@job_bp.get("/api/jobs/<job_id>")
@jwt_required
def get_job(job_id):
    """获取任务详情"""
    try:
        job = Job.query.filter_by(job_id=job_id, user_id=g.user_id).first()
        if job is None:
            return jsonify({"error": "任务不存在"}), 404
        return jsonify(job.to_dict())
    except Exception as e:
        logger.error(f"获取任务详情异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@job_bp.delete("/api/jobs/<job_id>")
@jwt_required
def delete_job(job_id):
    """删除任务（包括磁盘文件）"""
    try:
        job = Job.query.filter_by(job_id=job_id, user_id=g.user_id).first()
        if job is None:
            return jsonify({"error": "任务不存在"}), 404

        # 删除磁盘文件
        import shutil
        upload_dir = os.path.join(UPLOAD_DIR, job_id)
        job_dir = os.path.join(JOB_DIR, job_id)
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir, ignore_errors=True)
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)

        db.session.delete(job)
        db.session.commit()

        logger.info(f"删除任务: job_id={job_id}")
        return jsonify({"message": "任务已删除"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除任务异常: {str(e)}")
        return jsonify({"error": str(e)}), 500
