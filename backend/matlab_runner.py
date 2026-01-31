import threading
import logging
import os

logger = logging.getLogger(__name__)

_engine = None
_lock = threading.Lock()

def get_engine():
    """获取或启动MATLAB引擎"""
    global _engine
    with _lock:
        if _engine is None:
            try:
                logger.info("启动MATLAB引擎...")
                import matlab.engine
                _engine = matlab.engine.start_matlab()
                logger.info("MATLAB引擎启动成功")
            except Exception as e:
                logger.error(f"启动MATLAB引擎失败: {str(e)}")
                raise
        return _engine

def run_matlab_detect(matlab_dir: str, ndvi_path: str, coal_path: str, out_dir: str, startyear: int):
    """
    调用MATLAB detectMiningDisturbance函数

    参数:
        matlab_dir: MATLAB脚本目录
        ndvi_path: NDVI GeoTIFF文件路径
        coal_path: 裸煤概率GeoTIFF文件路径
        out_dir: 输出目录
        startyear: 起始年份

    返回:
        包含输出文件路径的字典
    """
    try:
        # 验证输入文件
        if not os.path.exists(ndvi_path):
            raise FileNotFoundError(f"NDVI文件不存在: {ndvi_path}")
        if not os.path.exists(coal_path):
            raise FileNotFoundError(f"裸煤文件不存在: {coal_path}")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        logger.info(f"MATLAB参数:")
        logger.info(f"  MATLAB目录: {matlab_dir}")
        logger.info(f"  NDVI路径: {ndvi_path}")
        logger.info(f"  裸煤路径: {coal_path}")
        logger.info(f"  输出目录: {out_dir}")
        logger.info(f"  起始年份: {startyear}")

        eng = get_engine()

        # 添加MATLAB脚本路径
        logger.info(f"添加MATLAB路径: {matlab_dir}")
        eng.addpath(matlab_dir, nargout=0)

        # 调用MATLAB函数
        logger.info("调用MATLAB函数: detectMiningDisturbance()")
        outputs = eng.detectMiningDisturbance(
            ndvi_path,
            coal_path,
            out_dir,
            float(startyear),
            nargout=1
        )

        logger.info("MATLAB函数执行成功")
        logger.info(f"输出文件:")
        logger.info(f"  mask: {outputs['mask']}")
        logger.info(f"  disturbance_year: {outputs['disturbance_year']}")
        logger.info(f"  recovery_year: {outputs['recovery_year']}")

        return {
            "mask": str(outputs["mask"]),
            "disturbance_year": str(outputs["disturbance_year"]),
            "recovery_year": str(outputs["recovery_year"]),
            "potential": str(outputs["potential"]),
            "res_type": str(outputs["res_type"]),
            "year_disturb_raw": str(outputs["year_disturb_raw"]),
            "year_recovery_raw": str(outputs["year_recovery_raw"]),
        }
    except Exception as e:
        logger.error(f"MATLAB执行异常: {str(e)}")
        raise
