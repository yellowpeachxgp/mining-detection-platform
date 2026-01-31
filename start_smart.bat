@echo off
REM 智能启动脚本 - 自动检测Python路径
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Mining Platform Launcher
echo ============================================================
echo.

REM 检查是否已保存Python路径
set PYTHON_PATH=
if exist "python_path.txt" (
    for /f "tokens=*" %%i in (python_path.txt) do set PYTHON_PATH=%%i
)

REM 如果没有保存路径，尝试自动查找
if "!PYTHON_PATH!"=="" (
    echo [1/3] Python path not configured, searching...
    for /f "tokens=*" %%i in ('where python.exe 2^>nul') do (
        set PYTHON_PATH=%%i
        goto :python_found
    )
)

:python_found
if "!PYTHON_PATH!"=="" (
    echo.
    echo ERROR: Python not found!
    echo.
    echo Solution 1: Run check_environment.py first
    echo   python check_environment.py
    echo.
    echo Solution 2: Install Python from:
    echo   https://www.anaconda.com/download
    echo   or https://www.python.org/downloads/
    echo.
    echo Solution 3: Make sure Python is in your PATH
    echo.
    pause
    exit /b 1
)

echo [1/3] Found Python: !PYTHON_PATH!

REM 检查依赖
echo.
echo [2/3] Checking dependencies...
!PYTHON_PATH! -c "import flask, numpy, rasterio, pyproj" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Missing dependencies, installing...
    cd /d "%~dp0\backend"
    echo Installing from requirements.txt...
    !PYTHON_PATH! -m pip install -q -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Try running: pip install flask flask-cors numpy rasterio pyproj
        pause
        exit /b 1
    )
    echo OK: Dependencies installed
)

REM 启动应用
echo.
echo [3/3] Starting Flask server...
echo.
cd /d "%~dp0\backend"
echo Server directory: %cd%
echo Web address: http://127.0.0.1:5000
echo Press Ctrl+C to stop
echo.
echo ============================================================
echo.

!PYTHON_PATH! run_app.py

pause
