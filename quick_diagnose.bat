@echo off
REM 矿区检测平台 - 快速诊断脚本 (Windows)
REM 用途: 快速检查后端是否运行、是否能上传文件

chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║  露天矿区检测平台 - 快速诊断脚本                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM 检查后端是否运行
echo [检查1] 后端服务连接...
curl -s http://127.0.0.1:5000 >nul 2>&1
if errorlevel 1 (
    echo ❌ 后端未运行
    echo.
    echo 请先启动后端:
    echo   1. 双击 start.bat
    echo   2. 或在PowerShell中运行: E:\Anaconda\python.exe backend\run_app.py
    pause
    exit /b 1
)
echo ✓ 后端服务运行正常

REM 检查data目录
echo.
echo [检查2] 项目结构...
if not exist "data\" (
    echo ❌ data目录不存在，正在创建...
    mkdir data\uploads
    mkdir data\jobs
)
if not exist "data\uploads\" mkdir data\uploads
if not exist "data\jobs\" mkdir data\jobs
echo ✓ data目录结构正常

REM 检查Python
echo.
echo [检查3] Python环境...
where E:\Anaconda\python.exe >nul 2>&1
if errorlevel 1 (
    echo ❌ Anaconda Python未找到
    pause
    exit /b 1
)
echo ✓ Python环境正常

REM 运行Python诊断脚本
echo.
echo [检查4] 运行诊断脚本...
echo.
E:\Anaconda\python.exe diagnostic_tool.py

pause
