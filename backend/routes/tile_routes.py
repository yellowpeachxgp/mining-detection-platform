"""瓦片和 GeoJSON 服务路由蓝图"""
import os
import io
import logging
import numpy as np
import rasterio
from rasterio.features import shapes
from pyproj import Transformer
from flask import Blueprint, jsonify, send_file
from config import JOB_DIR
from services.tile_service import (
    get_tile_cache_key, get_cached_tile, cache_tile,
    make_transparent_tile, render_tile, LAYER_FILES,
)

logger = logging.getLogger(__name__)
tile_bp = Blueprint("tile", __name__)

GEOJSON_LAYER_FILES = {
    "disturbance_mask": "mining_disturbance_mask.tif",
    "disturbance_year": "mining_disturbance_year.tif",
    "recovery_year": "mining_recovery_year.tif",
}


@tile_bp.get("/api/tiles/<job_id>/<layer_name>/<int:z>/<int:x>/<int:y>.png")
def serve_tile(job_id, layer_name, z, x, y):
    """提供动态栅格瓦片"""
    try:
        cache_key = get_tile_cache_key(job_id, layer_name, z, x, y)
        cached = get_cached_tile(cache_key)
        if cached:
            return send_file(io.BytesIO(cached), mimetype="image/png")

        if layer_name not in LAYER_FILES:
            return send_file(io.BytesIO(make_transparent_tile()), mimetype="image/png")

        tif_path = os.path.join(JOB_DIR, job_id, LAYER_FILES[layer_name])
        if not os.path.exists(tif_path):
            return send_file(io.BytesIO(make_transparent_tile()), mimetype="image/png")

        png_bytes = render_tile(tif_path, layer_name, z, x, y)
        cache_tile(cache_key, png_bytes)
        return send_file(io.BytesIO(png_bytes), mimetype="image/png")

    except Exception as e:
        logger.error(f"瓦片生成错误: {str(e)}")
        return send_file(io.BytesIO(make_transparent_tile()), mimetype="image/png")


@tile_bp.get("/api/result-geojson/<job_id>/<layer_name>")
def result_geojson(job_id, layer_name):
    """将栅格结果转换为 GeoJSON 多边形"""
    try:
        if layer_name not in GEOJSON_LAYER_FILES:
            return jsonify({"error": f"不支持的图层: {layer_name}"}), 400

        tif_path = os.path.join(JOB_DIR, job_id, GEOJSON_LAYER_FILES[layer_name])
        if not os.path.exists(tif_path):
            return jsonify({"error": f"文件不存在: {GEOJSON_LAYER_FILES[layer_name]}"}), 404

        features = []
        with rasterio.open(tif_path) as ds:
            data = ds.read(1)
            src_crs = ds.crs
            transform = ds.transform
            nodata = ds.nodata

            if nodata is not None:
                mask = (data != nodata) & (data != 0)
            else:
                mask = data != 0

            for geom, value in shapes(data.astype(np.int32), mask=mask, transform=transform):
                if value == 0:
                    continue

                if src_crs is not None and src_crs.to_string() != "EPSG:4326":
                    tfm = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
                    coords = geom["coordinates"]
                    new_coords = []
                    for ring in coords:
                        new_ring = []
                        for x_c, y_c in ring:
                            lon, lat = tfm.transform(x_c, y_c)
                            new_ring.append([lon, lat])
                        new_coords.append(new_ring)
                    geom["coordinates"] = new_coords

                feature = {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {"value": int(value), "layer": layer_name},
                }

                if "year" in layer_name:
                    feature["properties"]["year"] = int(value)

                features.append(feature)

        logger.info(f"GeoJSON转换成功: {job_id}/{layer_name}, {len(features)}个要素")
        return jsonify({"type": "FeatureCollection", "features": features})

    except Exception as e:
        logger.error(f"GeoJSON转换异常: {str(e)}")
        return jsonify({"error": f"转换失败: {str(e)}"}), 500
