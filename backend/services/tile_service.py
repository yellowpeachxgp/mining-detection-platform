"""瓦片服务 — 从 app.py 抽取"""
import io
import math
import logging
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds, calculate_default_transform, reproject
from rasterio.enums import Resampling
from PIL import Image

logger = logging.getLogger(__name__)

TILE_SIZE = 256
EARTH_RADIUS = 6378137.0
ORIGIN_SHIFT = 2 * math.pi * EARTH_RADIUS / 2.0

# 简单内存瓦片缓存
_tile_cache = {}
_tile_cache_max = 500


def tile_bounds_3857(z, x, y):
    """计算瓦片在 Web Mercator (EPSG:3857) 中的边界"""
    res = 2 * ORIGIN_SHIFT / (TILE_SIZE * (2 ** z))
    minx = -ORIGIN_SHIFT + x * TILE_SIZE * res
    maxx = minx + TILE_SIZE * res
    maxy = ORIGIN_SHIFT - y * TILE_SIZE * res
    miny = maxy - TILE_SIZE * res
    return (minx, miny, maxx, maxy)


def get_tile_cache_key(job_id, layer_name, z, x, y):
    return f"{job_id}:{layer_name}:{z}:{x}:{y}"


def cache_tile(key, png_bytes):
    global _tile_cache
    if len(_tile_cache) >= _tile_cache_max:
        keys_to_remove = list(_tile_cache.keys())[: int(_tile_cache_max * 0.2)]
        for k in keys_to_remove:
            del _tile_cache[k]
    _tile_cache[key] = png_bytes


def get_cached_tile(key):
    return _tile_cache.get(key)


LAYER_COLORMAPS = {
    "disturbance_mask": {"type": "categorical", "colors": {0: (0, 0, 0, 0), 1: (220, 38, 38, 180)}},
    "disturbance_year": {"type": "year_gradient", "start": (255, 100, 100), "end": (139, 0, 0), "range": (1980, 2050)},
    "recovery_year": {"type": "year_gradient", "start": (144, 238, 144), "end": (0, 100, 0), "range": (1980, 2050)},
    "potential_disturbance": {"type": "continuous", "color": (255, 165, 0)},
    "res_disturbance_type": {"type": "categorical_range"},
}

LAYER_FILES = {
    "disturbance_mask": "mining_disturbance_mask.tif",
    "disturbance_year": "mining_disturbance_year.tif",
    "recovery_year": "mining_recovery_year.tif",
    "potential_disturbance": "potential_disturbance.tif",
    "res_disturbance_type": "res_disturbance_type.tif",
}


def apply_colormap(data, layer_name, nodata=None):
    """将栅格数据转换为 RGBA 图像数组"""
    h, w = data.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    config = LAYER_COLORMAPS.get(layer_name, {"type": "default"})

    valid = np.ones((h, w), dtype=bool)
    if nodata is not None:
        valid = valid & (data != nodata)
    valid = valid & ~np.isnan(data) & (data != 0)

    if config["type"] == "categorical":
        for val, color in config["colors"].items():
            mask = (data == val) & valid
            rgba[mask] = color

    elif config["type"] == "year_gradient":
        y_min, y_max = config["range"]
        start = np.array(config["start"])
        end = np.array(config["end"])
        normalized = np.clip((data - y_min) / (y_max - y_min), 0, 1)
        for c in range(3):
            rgba[valid, c] = (start[c] + normalized[valid] * (end[c] - start[c])).astype(np.uint8)
        rgba[valid, 3] = 180

    elif config["type"] == "continuous":
        color = config["color"]
        rgba[valid, 0] = color[0]
        rgba[valid, 1] = color[1]
        rgba[valid, 2] = color[2]
        max_val = np.nanmax(data[valid]) if np.any(valid) else 1
        if max_val > 0:
            rgba[valid, 3] = (150 * np.minimum(data[valid] / max_val, 1)).astype(np.uint8)

    else:
        rgba[valid, 0] = ((data[valid] * 37) % 200 + 55).astype(np.uint8)
        rgba[valid, 1] = ((data[valid] * 73) % 200 + 55).astype(np.uint8)
        rgba[valid, 2] = ((data[valid] * 113) % 200 + 55).astype(np.uint8)
        rgba[valid, 3] = 180

    return rgba


def make_transparent_tile():
    """生成透明 PNG 瓦片的字节"""
    img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def render_tile(tif_path, layer_name, z, x, y):
    """渲染一个瓦片，返回 PNG 字节"""
    tile_b = tile_bounds_3857(z, x, y)

    with rasterio.open(tif_path) as src:
        src_bounds = transform_bounds("EPSG:3857", src.crs, *tile_b)

        data_bounds = src.bounds
        if (
            src_bounds[2] < data_bounds.left
            or src_bounds[0] > data_bounds.right
            or src_bounds[3] < data_bounds.bottom
            or src_bounds[1] > data_bounds.top
        ):
            return make_transparent_tile()

        window = from_bounds(*src_bounds, src.transform)

        row_off = max(0, int(window.row_off))
        col_off = max(0, int(window.col_off))
        row_end = min(src.height, int(window.row_off + window.height))
        col_end = min(src.width, int(window.col_off + window.width))

        if row_end <= row_off or col_end <= col_off:
            return make_transparent_tile()

        read_window = Window(col_off, row_off, col_end - col_off, row_end - row_off)
        data = src.read(1, window=read_window)
        window_transform = src.window_transform(read_window)

        dst_transform, dst_width, dst_height = calculate_default_transform(
            src.crs,
            "EPSG:3857",
            data.shape[1],
            data.shape[0],
            *src_bounds,
            dst_width=TILE_SIZE,
            dst_height=TILE_SIZE,
        )

        dst_data = np.zeros((TILE_SIZE, TILE_SIZE), dtype=data.dtype)

        reproject(
            source=data,
            destination=dst_data,
            src_transform=window_transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs="EPSG:3857",
            resampling=Resampling.nearest,
        )

        rgba = apply_colormap(dst_data, layer_name, src.nodata)

    img = Image.fromarray(rgba, "RGBA")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
