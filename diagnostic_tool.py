#!/usr/bin/env python
"""
矿区检测平台 - 诊断和测试工具
用途: 检查文件上传、MATLAB处理、结果验证
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# 颜色输出
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{Color.BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Color.RESET}\n")

def print_success(text):
    print(f"{Color.GREEN}✓ {text}{Color.RESET}")

def print_error(text):
    print(f"{Color.RED}✗ {text}{Color.RESET}")

def print_warning(text):
    print(f"{Color.YELLOW}⚠ {text}{Color.RESET}")

def print_info(text):
    print(f"{Color.BLUE}ℹ {text}{Color.RESET}")

# 配置
BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 300  # 5分钟超时

def check_backend():
    """检查后端是否在运行"""
    print_header("步骤1: 检查后端服务")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print_success("后端服务正在运行")
            return True
        else:
            print_error(f"后端返回状态码 {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"无法连接到 {BASE_URL}")
        print_info("请先启动后端: 双击 start.bat 或运行 python run_app.py")
        return False
    except Exception as e:
        print_error(f"连接失败: {str(e)}")
        return False

def test_upload(ndvi_path, coal_path):
    """测试文件上传"""
    print_header("步骤2: 测试文件上传")

    # 检查文件是否存在
    if not os.path.exists(ndvi_path):
        print_error(f"NDVI文件不存在: {ndvi_path}")
        return None
    if not os.path.exists(coal_path):
        print_error(f"裸煤文件不存在: {coal_path}")
        return None

    file_size_ndvi = os.path.getsize(ndvi_path) / (1024*1024)
    file_size_coal = os.path.getsize(coal_path) / (1024*1024)

    print_info(f"NDVI文件大小: {file_size_ndvi:.2f} MB")
    print_info(f"裸煤文件大小: {file_size_coal:.2f} MB")
    print_info("正在上传NDVI文件...")

    try:
        # 上传NDVI
        with open(ndvi_path, 'rb') as f:
            files = {'file': f}
            data = {'kind': 'ndvi'}
            response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data, timeout=60)

        if response.status_code != 200:
            print_error(f"NDVI上传失败: {response.text}")
            return None

        result_ndvi = response.json()
        job_id = result_ndvi.get('job_id')
        print_success(f"NDVI上传成功, job_id: {job_id}")

        # 上传裸煤
        print_info("正在上传裸煤概率文件...")
        with open(coal_path, 'rb') as f:
            files = {'file': f}
            data = {'kind': 'coal', 'job_id': job_id}
            response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data, timeout=60)

        if response.status_code != 200:
            print_error(f"裸煤上传失败: {response.text}")
            return None

        result_coal = response.json()
        print_success(f"裸煤上传成功")

        return job_id

    except requests.exceptions.Timeout:
        print_error("上传超时 (>60秒)")
        return None
    except Exception as e:
        print_error(f"上传异常: {str(e)}")
        return None

def test_detection(job_id, startyear=2010):
    """测试MATLAB检测"""
    print_header("步骤3: 启动MATLAB检测")

    print_info(f"job_id: {job_id}")
    print_info(f"起始年份: {startyear}")
    print_info("正在调用MATLAB函数...")
    print_warning("这可能需要几分钟，请耐心等待...")

    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/run",
            json={'job_id': job_id, 'startyear': startyear},
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time

        if response.status_code != 200:
            print_error(f"检测失败: {response.text}")
            return None

        result = response.json()
        print_success(f"MATLAB检测完成 (耗时: {elapsed:.1f}秒)")

        return result

    except requests.exceptions.Timeout:
        print_error(f"检测超时 (>300秒)")
        return None
    except Exception as e:
        print_error(f"检测异常: {str(e)}")
        return None

def check_output_files(job_id):
    """检查输出文件是否生成"""
    print_header("步骤4: 验证输出文件")

    job_dir = Path(f"data/jobs/{job_id}")

    if not job_dir.exists():
        print_error(f"结果目录不存在: {job_dir}")
        return False

    expected_files = [
        'mining_disturbance_mask.tif',
        'mining_disturbance_year.tif',
        'mining_recovery_year.tif',
        'potential_disturbance.tif',
        'res_disturbance_type.tif',
        'year_disturbance_raw.tif',
        'year_recovery_raw.tif'
    ]

    all_exist = True
    for filename in expected_files:
        filepath = job_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size / (1024*1024)
            print_success(f"{filename} ({size:.2f} MB)")
        else:
            print_error(f"{filename} (缺失)")
            all_exist = False

    return all_exist

def test_timeseries_query(job_id, lon, lat):
    """测试时间序列查询"""
    print_header("步骤5: 测试时间序列查询")

    print_info(f"查询坐标: lon={lon}, lat={lat}")

    try:
        response = requests.get(
            f"{BASE_URL}/api/ndvi-timeseries",
            params={'job_id': job_id, 'lon': lon, 'lat': lat},
            timeout=10
        )

        if response.status_code != 200:
            print_error(f"查询失败: {response.text}")
            return False

        data = response.json()
        print_success("时间序列查询成功")

        print_info(f"波段数: {len(data['years'])}")
        print_info(f"年份范围: {data['years'][0]}-{data['years'][-1]}")
        print_info(f"NDVI值范围: {min(data['ndvi']):.3f} - {max(data['ndvi']):.3f}")
        print_info(f"扰动年份: {data['disturbance_year'] or '无'}")
        print_info(f"恢复年份: {data['recovery_year'] or '无'}")

        return True

    except Exception as e:
        print_error(f"查询异常: {str(e)}")
        return False

def main():
    print(f"\n{Color.BLUE}")
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  露天矿区检测平台 - 诊断和测试工具                    ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print(f"{Color.RESET}")

    # 检查后端
    if not check_backend():
        print_error("\n后端服务未运行，请先启动:")
        print_info("  Windows: 双击 start.bat")
        print_info("  Linux/Mac: bash start.sh")
        return

    # 获取输入
    print_header("配置")

    ndvi_path = input("请输入NDVI GeoTIFF文件路径 (或直接回车使用示例): ").strip()
    if not ndvi_path:
        ndvi_path = "test_ndvi.tif"
        print_warning(f"使用示例路径: {ndvi_path}")

    coal_path = input("请输入裸煤概率GeoTIFF文件路径 (或直接回车使用示例): ").strip()
    if not coal_path:
        coal_path = "test_coal.tif"
        print_warning(f"使用示例路径: {coal_path}")

    startyear = input("请输入起始年份 (默认2010): ").strip()
    try:
        startyear = int(startyear) if startyear else 2010
    except ValueError:
        startyear = 2010

    # 运行诊断
    job_id = test_upload(ndvi_path, coal_path)
    if not job_id:
        print_error("\n文件上传失败，诊断终止")
        return

    result = test_detection(job_id, startyear)
    if not result:
        print_error("\nMALAB检测失败，诊断终止")
        return

    check_output_files(job_id)

    # 测试查询 (使用默认坐标)
    lon = 110.5
    lat = 35.5
    test_timeseries_query(job_id, lon, lat)

    # 总结
    print_header("诊断完成")
    print_success("所有测试完成！")
    print_info(f"job_id: {job_id}")
    print_info(f"结果存储在: data/jobs/{job_id}/")
    print_info("可以在浏览器中访问地图查看可视化结果")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}用户中断{Color.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
