"""地理空间处理服务 — 从 app.py 抽取"""
import logging
import numpy as np
import rasterio
from pyproj import Transformer

logger = logging.getLogger(__name__)


def get_crs_info(geotiff_path):
    """提取 GeoTIFF 的坐标系信息用于前端显示"""
    try:
        with rasterio.open(geotiff_path) as ds:
            if ds.crs is None:
                return {"valid": False, "warning": "GeoTIFF 缺少坐标系元数据"}

            epsg = ds.crs.to_epsg()
            crs_string = ds.crs.to_string()

            epsg_names = {
                4326: "WGS 84 地理坐标系",
                3857: "Web Mercator",
                4490: "CGCS2000 地理坐标系",
            }

            crs_name = None
            if epsg:
                crs_name = epsg_names.get(epsg)
                if not crs_name:
                    if 32601 <= epsg <= 32660:
                        crs_name = f"WGS 84 / UTM {epsg - 32600}N"
                    elif 32701 <= epsg <= 32760:
                        crs_name = f"WGS 84 / UTM {epsg - 32700}S"
                    elif 4500 <= epsg <= 4554:
                        crs_name = f"CGCS2000 高斯投影 {epsg - 4500}"

            return {
                "valid": True,
                "epsg": epsg,
                "crs_string": crs_string,
                "crs_name": crs_name or crs_string,
                "warning": None,
            }
    except Exception as e:
        return {"valid": False, "warning": f"读取坐标系失败: {str(e)}"}


def get_geotiff_bounds(geotiff_path):
    """获取 GeoTIFF 的地理边界 (EPSG:4326)"""
    try:
        with rasterio.open(geotiff_path) as ds:
            bounds = ds.bounds
            src_crs = ds.crs

            if src_crs is None or src_crs.to_string() == "EPSG:4326":
                return {
                    "west": bounds.left,
                    "south": bounds.bottom,
                    "east": bounds.right,
                    "north": bounds.top,
                }
            else:
                tfm = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
                west, south = tfm.transform(bounds.left, bounds.bottom)
                east, north = tfm.transform(bounds.right, bounds.top)
                return {"west": west, "south": south, "east": east, "north": north}
    except Exception as e:
        logger.warning(f"获取边界失败: {str(e)}")
        return None


def sample_timeseries(geotiff_path, lon, lat):
    """从 GeoTIFF 中采样时间序列数据"""
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

        if row < 0 or row >= ds.height or col < 0 or col >= ds.width:
            raise ValueError(f"坐标 ({lon}, {lat}) 超出数据范围")

        arr = ds.read()
        vals = arr[:, row, col].astype("float64")

        nodata = ds.nodata
        if nodata is not None:
            vals = np.where(vals == nodata, np.nan, vals)

        vals_list = []
        for v in vals:
            if np.isnan(v) or np.isinf(v):
                vals_list.append(None)
            else:
                vals_list.append(float(v))

        logger.info(f"采样成功: {geotiff_path} at ({lon}, {lat}), {ds.count}个波段")
        return vals_list, ds.count


def sample_singleband(geotiff_path, lon, lat):
    """从单波段 GeoTIFF 中采样"""
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

            if row < 0 or row >= ds.height or col < 0 or col >= ds.width:
                return None

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


def format_file_size(size_bytes):
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
