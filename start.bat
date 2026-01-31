@echo off
REM 简化版启动脚本 - 兼容性更好
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Mining Platform - Quick Start
echo ============================================================
echo.

REM 方法1: 查找conda环境的Python
set PYTHON_PATH=
for /f "tokens=*" %%i in ('where python.exe 2^>nul') do set PYTHON_PATH=%%i

if "!PYTHON_PATH!"=="" (
    echo ERROR: Python not found in PATH
    echo.
    echo Please install Python or add it to PATH
    echo Download: https://www.anaconda.com/download
    echo.
    pause
    exit /b 1
)

echo [1/3] Found Python: !PYTHON_PATH!

REM 检查依赖
echo.
echo [2/3] Checking dependencies...
!PYTHON_PATH! -c "import flask, numpy, rasterio, pyproj; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Missing dependencies, installing...
    cd /d "%~dp0\backend"
    !PYTHON_PATH! -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM 启动应用
echo.
echo [3/3] Starting Flask server...
echo.
cd /d "%~dp0\backend"
echo Working directory: %cd%
echo Access at: http://127.0.0.1:5000
echo Press Ctrl+C to stop
echo.
echo ============================================================
echo.

!PYTHON_PATH! run_app.py

pause