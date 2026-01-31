import os
import uuid
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import rasterio
from pyproj import Transformer

from config import UPLOAD_DIR, JOB_DIR, MATLAB_DIR
from matlab_runner import run_matlab_detect

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(JOB_DIR, exist_ok=True)

logger.info(f"UPLOAD_DIR: {UPLOAD_DIR}")
logger.info(f"JOB_DIR: {JOB_DIR}")
logger.info(f"MATLAB_DIR: {MATLAB_DIR}")

def sample_timeseries(geotiff_path, lon, lat):
    """从GeoTIFF中采样时间序列数据"""
    try:
        with rasterio.open(geotiff_path) as ds:
            src_crs = ds.crs
            if src_crs is None:
                raise ValueError("GeoTIFF 没有 CRS 信息")

            if src_crs.to_string() != "EPSG:4326":
                tfm = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
                x, y = tfm.transform(lon, lat)
            else:
                x, y = lon, lat

            row, col = ds.index(x, y)
            arr = ds.read()  # (bands, rows, cols)
            vals = arr[:, row, col].astype("float32")

            nodata = ds.nodata
            if nodata is not None:
                vals = np.where(vals == nodata, np.nan, vals)

            logger.info(f"采样成功: {geotiff_path} at ({lon}, {lat}), {ds.count}个波段")
            return vals.tolist(), ds.count
    except Exception as e:
        logger.error(f"采样失败: {str(e)}")
        raise

def sample_singleband(geotiff_path, lon, lat):
    """从单波段GeoTIFF中采样"""
    try:
        with rasterio.open(geotiff_path) as ds:
            src_crs = ds.crs
            if src_crs is None:
                raise ValueError("GeoTIFF 没有 CRS 信息")

            if src_crs.to_string() != "EPSG:4326":
                tfm = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
                x, y = tfm.transform(lon, lat)
            else:
                x, y = lon, lat

            row, col = ds.index(x, y)
            val = ds.read(1)[row, col].item()
            nodata = ds.nodata
            if nodata is not None and val == nodata:
                return None
            if val == 0:
                return None
            return int(val)
    except Exception as e:
        logger.warning(f"采样单波段失败: {str(e)}")
        return None

@app.post("/api/upload")
def upload():
    """上传GeoTIFF文件"""
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

        logger.info(f"上传成功: job_id={job_id}, kind={kind}, path={path}")
        return jsonify({"job_id": job_id, "kind": kind, "path": path})
    except Exception as e:
        logger.error(f"上传异常: {str(e)}")
        return jsonify({"error": f"上传失败: {str(e)}"}), 500

@app.post("/api/run")
def run_job():
    """执行MATLAB检测"""
    try:
        data = request.get_json(force=True)
        job_id = data.get("job_id")
        startyear = int(data.get("startyear", 2010))

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

        logger.info(f"开始MATLAB检测: job_id={job_id}, startyear={startyear}")
        result = run_matlab_detect(MATLAB_DIR, ndvi_path, coal_path, out_dir, startyear)
        logger.info(f"MATLAB检测完成: job_id={job_id}")

        def url_for(name):
            return f"/jobs/{job_id}/{name}"

        return jsonify({
            "job_id": job_id,
            "outputs": {
                "mining_disturbance_mask": url_for("mining_disturbance_mask.tif"),
                "mining_disturbance_year": url_for("mining_disturbance_year.tif"),
                "mining_recovery_year": url_for("mining_recovery_year.tif"),
                "potential_disturbance": url_for("potential_disturbance.tif"),
                "res_disturbance_type": url_for("res_disturbance_type.tif"),
                "year_disturbance_raw": url_for("year_disturbance_raw.tif"),
                "year_recovery_raw": url_for("year_recovery_raw.tif"),
            }
        })
    except Exception as e:
        logger.error(f"MATLAB检测异常: {str(e)}")
        return jsonify({"error": f"检测失败: {str(e)}"}), 500

@app.get("/api/ndvi-timeseries")
def ndvi_timeseries():
    """查询NDVI时间序列"""
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
            "recovery_year": recovery_year
        })
    except Exception as e:
        logger.error(f"查询异常: {str(e)}")
        return jsonify({"error": f"查询失败: {str(e)}"}), 500

@app.get("/")
def home():
    """提供前端页面"""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    return send_from_directory(frontend_dir, "index.html")

@app.get("/<path:path>")
def frontend_static(path):
    """提供前端静态资源"""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    if os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return jsonify({"error": "not found"}), 404

@app.get("/jobs/<job_id>/<filename>")
def serve_job_file(job_id, filename):
    """提供结果文件"""
    try:
        d = os.path.join(JOB_DIR, job_id)
        logger.info(f"获取结果文件: {job_id}/{filename}")
        return send_from_directory(d, filename, as_attachment=False)
    except Exception as e:
        logger.error(f"获取文件异常: {str(e)}")
        return jsonify({"error": f"文件不存在: {str(e)}"}), 404

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "请求的资源不存在"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"服务器错误: {str(e)}")
    return jsonify({"error": "服务器内部错误"}), 500

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("启动露天矿区检测平台")
    logger.info("访问地址: http://127.0.0.1:5000")
    logger.info("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=False)

