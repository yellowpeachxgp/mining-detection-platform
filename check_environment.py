#!/usr/bin/env python
"""
检测Python和环境配置 - 帮助诊断启动问题
"""

import os
import sys
import subprocess
from pathlib import Path

def find_python_paths():
    """查找系统中所有Python安装"""
    paths = []

    # 方法1: 使用where命令
    try:
        result = subprocess.run(['where', 'python.exe'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            for path in result.stdout.strip().split('\n'):
                if path:
                    paths.append(path)
    except:
        pass

    # 方法2: 常见安装位置
    common_locations = [
        'C:\\Anaconda\\python.exe',
        'C:\\Anaconda3\\python.exe',
        'C:\\Users\\*\\Anaconda\\python.exe',
        'C:\\Users\\*\\Anaconda3\\python.exe',
        'D:\\Anaconda\\python.exe',
        'D:\\Anaconda3\\python.exe',
        'E:\\Anaconda\\python.exe',
        'E:\\Anaconda3\\python.exe',
        'C:\\Program Files\\Python*\\python.exe',
        'C:\\Program Files (x86)\\Python*\\python.exe',
    ]

    for pattern in common_locations:
        if '*' in pattern:
            # 处理通配符
            import glob
            matches = glob.glob(pattern)
            paths.extend(matches)
        else:
            if os.path.exists(pattern):
                paths.append(pattern)

    return list(set(paths))  # 去重

def check_version(python_path):
    """检查Python版本"""
    try:
        result = subprocess.run([python_path, '--version'],
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except:
        return None

def check_modules(python_path):
    """检查必要的模块"""
    modules = ['flask', 'numpy', 'rasterio', 'pyproj']
    installed = []
    missing = []

    for module in modules:
        try:
            subprocess.run([python_path, '-c', f'import {module}'],
                         capture_output=True, timeout=5, check=True)
            installed.append(module)
        except:
            missing.append(module)

    return installed, missing

def main():
    print("\n" + "="*60)
    print("  Python Environment Diagnostic Tool")
    print("="*60 + "\n")

    # 查找Python
    print("[1/3] Searching for Python installations...\n")
    pythons = find_python_paths()

    if not pythons:
        print("ERROR: No Python found!")
        print("\nPlease install Python:")
        print("  - Download: https://www.anaconda.com/download")
        print("  - Or: https://www.python.org/downloads/")
        return False

    print(f"Found {len(pythons)} Python installation(s):\n")
    for i, path in enumerate(pythons, 1):
        version = check_version(path)
        status = "OK" if version else "ERROR"
        print(f"  {i}. {path}")
        if version:
            print(f"     Version: {version}")

    # 使用第一个Python
    python_path = pythons[0]
    print(f"\nUsing: {python_path}\n")

    # 检查模块
    print("[2/3] Checking required modules...\n")
    installed, missing = check_modules(python_path)

    if installed:
        print("Installed modules:")
        for mod in installed:
            print(f"  ✓ {mod}")

    if missing:
        print("\nMissing modules:")
        for mod in missing:
            print(f"  ✗ {mod}")
        print("\nYou can install them with:")
        print(f"  {python_path} -m pip install {' '.join(missing)}")

    # 保存Python路径
    print("\n[3/3] Saving configuration...\n")
    config_file = Path(__file__).parent / 'python_path.txt'
    config_file.write_text(python_path)
    print(f"Python path saved to: {config_file}")
    print(f"Content: {python_path}\n")

    # 显示结果
    print("="*60)
    if installed and not missing:
        print("✓ Environment is ready to use!")
        print("\nYou can now run: start.bat")
    else:
        print("⚠ Some issues detected")
        if missing:
            print("\nRun this to install missing modules:")
            print(f"  {python_path} -m pip install -r backend\\requirements.txt")
    print("="*60 + "\n")

    return not bool(missing)

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
