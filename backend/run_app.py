#!/usr/bin/env python
"""
启动脚本：使用Anaconda Python运行Flask应用
"""
import sys
import os

# 确保使用Anaconda的Python
if 'Anaconda' not in sys.executable:
    print(f"警告：当前Python不是Anaconda的 ({sys.executable})")
    print("建议使用: E:\\Anaconda\\python.exe run_app.py")

# 导入并启动应用
from app import app

if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs('../data/uploads', exist_ok=True)
    os.makedirs('../data/jobs', exist_ok=True)
    
    # 启动Flask应用
    app.run(host='127.0.0.1', port=5000, debug=False)
