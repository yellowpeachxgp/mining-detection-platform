# 🔍 故障排除与系统诊断指南

## ✅ 前置检查清单

在启动平台前，运行此诊断脚本：

```bash
@echo off
setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║  露天矿区检测平台 - 系统诊断工具                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

echo [1/5] 检查Python版本...
E:\Anaconda\python.exe --version

echo.
echo [2/5] 检查核心Python依赖...
E:\Anaconda\python.exe -c "
import sys
deps = ['flask', 'numpy', 'rasterio', 'pyproj']
print('✓ Python版本: ' + sys.version.split()[0])
for dep in deps:
    try:
        mod = __import__(dep)
        print(f'✓ {dep}: {getattr(mod, \"__version__\", \"installed\")}')
    except ImportError:
        print(f'✗ {dep}: 未安装')
"

echo.
echo [3/5] 检查MATLAB引擎...
E:\Anaconda\python.exe -c "
try:
    import matlab.engine
    print('✓ MATLAB引擎: 可用')
except ImportError:
    print('✗ MATLAB引擎: 未安装')
    print('  解决方案: cd E:\Matlab2024b\extern\engines\python && python setup.py install')
"

echo.
echo [4/5] 检查MATLAB路径...
if exist "E:\Matlab2024b\" (
    echo ✓ MATLAB: 已找到 (E:\Matlab2024b)
) else (
    echo ✗ MATLAB: 未找到，请检查安装路径
)

echo.
echo [5/5] 检查项目结构...
if exist "matlab\" (echo ✓ matlab目录) else (echo ✗ matlab目录缺失)
if exist "frontend\" (echo ✓ frontend目录) else (echo ✗ frontend目录缺失)
if exist "backend\" (echo ✓ backend目录) else (echo ✗ backend目录缺失)
if exist "data\" (echo ✓ data目录) else (echo ✗ data目录缺失)

echo.
echo ═════════════════════════════════════════════════════════
echo 诊断完成！
pause
```

---

## 🐛 常见错误及解决方案

### 错误类型 1: Python/依赖相关

#### ❌ "ModuleNotFoundError: No module named 'flask'"
```
症状: 启动后立即报错
原因: Python依赖未安装或版本不兼容
解决:
  1. cd mining-platform/backend
  2. E:\Anaconda\python.exe -m pip install -r requirements.txt
  3. 重新启动 start.bat
```

#### ❌ "ImportError: No module named 'matlab.engine'"
```
症状: Flask启动但访问页面时错误
原因: MATLAB引擎未为Python安装
解决:
  1. 打开CMD (Win+R → cmd)
  2. cd E:\Matlab2024b\extern\engines\python
  3. E:\Anaconda\python.exe setup.py install
  4. 返回 mining-platform，重新启动 start.bat
```

#### ❌ "ModuleNotFoundError: No module named 'rasterio'"
```
症状: 上传GeoTIFF时报错
原因: rasterio库未安装或GDAL依赖缺失
解决:
  方式A (自动安装):
    cd mining-platform/backend
    E:\Anaconda\python.exe -m pip install rasterio

  方式B (使用conda安装，更稳定):
    E:\Anaconda\Scripts\conda install -c conda-forge rasterio
```

---

### 错误类型 2: MATLAB相关

#### ❌ "Error: Could not find MATLAB installation"
```
症状: 启动时卡在MATLAB连接
原因: MATLAB未安装或路径错误
解决:
  1. 确认MATLAB已安装: C:\Program Files\MATLAB\R2024b
  2. 重启后重试 (MATLAB许可证需要初始化)
  3. 或者在MATLAB中手动运行测试:
     >> detectMiningDisturbance('test.tif', 'test.tif', 'output', 2010)
```

#### ❌ "matlab.engine.MatlabExecutionError: ..."
```
症状: MATLAB函数执行时报错
原因: MATLAB脚本有错误或输入文件格式问题
解决:
  1. 检查GeoTIFF文件是否有效:
     - 使用GDAL工具检查: gdalinfo ndvi.tif
     - 检查是否有CRS: gdalinfo ndvi.tif | grep -i "crs\|srs"
  2. 检查MATLAB脚本 (matlab/detectMiningDisturbance.m)
  3. 查看后端日志获取详细错误信息
```

#### ❌ "matlab.engine.EngineError: Session interrupted"
```
症状: MATLAB引擎断开连接
原因: MATLAB许可证过期或内存溢出
解决:
  1. 重启 start.bat (会重新初始化MATLAB)
  2. 检查MATLAB许可证: matlab -c
  3. 使用较小的GeoTIFF文件进行测试
```

---

### 错误类型 3: GeoTIFF/地理数据相关

#### ❌ "GeoTIFF 没有 CRS 信息"
```
症状: 点击地图查询时报错
原因: GeoTIFF文件缺少空间参考系统
解决:
  使用GDAL工具添加CRS:
    gdalwarp -s_srs EPSG:4326 input.tif output.tif

  或使用Python修复:
    from rasterio.crs import CRS
    import rasterio
    with rasterio.open('input.tif') as src:
        profile = src.profile
        profile.update(crs=CRS.from_epsg(4326))
        with rasterio.open('output.tif', 'w', **profile) as dst:
            dst.write(src.read())
```

#### ❌ "IndexError: list index out of range"
```
症状: 点击地图坐标时报错
原因: 点击位置超出GeoTIFF范围或坐标系不匹配
解决:
  1. 确保点击位置在GeoTIFF范围内
  2. 检查坐标系统: gdalinfo ndvi.tif | grep -i "crs\|srs"
  3. 在ArcGIS中打开GeoTIFF验证地理位置
```

#### ❌ "IOError: [Errno 2] No such file or directory: 'ndvi.tif'"
```
症状: 运行检测时报错
原因: 文件未上传或路径错误
解决:
  1. 确保上传了两个文件 (ndvi.tif 和 coal.tif)
  2. 检查 data/uploads/<job_id>/ 目录是否存在
  3. 重新上传文件
```

---

### 错误类型 4: 前端/浏览器相关

#### ❌ 地图不显示
```
症状: 右侧viewDiv是空白的
原因: ArcGIS JS API加载失败或网络问题
解决:
  1. 检查网络连接
  2. 打开浏览器开发者工具 (F12 → Console)
  3. 查看网络错误: F12 → Network → 刷新页面
  4. 尝试更换浏览器或清除缓存 (Ctrl+Shift+Delete)
```

#### ❌ "Cannot read property 'click' of null"
```
症状: 页面加载失败，左侧面板不响应
原因: HTML DOM元素未加载或JavaScript错误
解决:
  1. 检查 frontend/index.html 是否完整
  2. 检查浏览器console (F12) 获取错误行号
  3. 硬刷新页面: Ctrl+Shift+R
```

#### ❌ "CORS error: Cross-Origin Request Blocked"
```
症状: 前端请求后端时报错
原因: 跨域资源共享配置问题
解决:
  1. 确认 backend/app.py 中有 CORS(app)
  2. 确认访问地址是 http://127.0.0.1:5000 (不要用 localhost)
  3. 重启后端服务
```

#### ❌ Chart.js 图表不显示
```
症状: 点击地图后左侧没有曲线图
原因: Chart.js库加载失败或数据问题
解决:
  1. 检查网络 (确保能访问 CDN)
  2. 打开 F12 → Network，查看 chart.js 是否成功加载
  3. 检查浏览器console是否有错误
  4. 尝试离线使用本地Chart.js库
```

---

### 错误类型 5: 性能/超时相关

#### ❌ "Request timeout" 或长时间无响应
```
症状: 点击"运行检测"后，10分钟还在加载
原因: 文件太大、MATLAB计算耗时、或进程卡死
解决:
  1. 查看任务管理器: 是否有 python.exe 和 MATLAB.exe 在运行
  2. 如果没有进程: 后端可能崩溃，检查终端日志
  3. 如果有进程: 耐心等待 (大文件可能需要 10-20 分钟)
  4. 如果超过20分钟: 关闭 start.bat，尝试更小的文件
```

#### ❌ "Out of memory" 或内存溢出
```
症状: MATLAB进程突然停止，后端报错
原因: GeoTIFF文件太大，超过可用内存
解决:
  1. 检查可用内存: 任务管理器 → 性能
  2. 关闭其他程序释放内存
  3. 使用GDAL下采样文件:
     gdal_translate -outsize 50% 50% input.tif output.tif
  4. 或使用更强力的计算机
```

---

## 🔧 调试工具和命令

### 1. 检查GeoTIFF文件信息

```bash
# 安装GDAL (如果未安装)
pip install gdal-utils

# 查看GeoTIFF元数据
gdalinfo ndvi.tif

# 示例输出应该包含:
# - Coordinate System
# - Size (像素行列)
# - Band count
```

### 2. 验证MATLAB函数

在MATLAB命令行运行测试：
```matlab
% 添加路径
addpath('F:\挑战杯\mining-platform\matlab')

% 运行函数
outputs = detectMiningDisturbance('ndvi.tif', 'coal.tif', 'output', 2010);

% 查看输出
disp(outputs)
```

### 3. 直接调用后端API

```bash
# 上传文件
curl -X POST http://127.0.0.1:5000/api/upload \
  -F "file=@ndvi.tif" \
  -F "kind=ndvi" \
  -F "job_id=test123"

# 运行检测
curl -X POST http://127.0.0.1:5000/api/run \
  -H "Content-Type: application/json" \
  -d "{\"job_id\":\"test123\",\"startyear\":2010}"

# 查询时间序列
curl "http://127.0.0.1:5000/api/ndvi-timeseries?job_id=test123&lon=110.5&lat=35.5"
```

### 4. 查看后端日志

```bash
# 重定向日志到文件
E:\Anaconda\python.exe run_app.py > debug.log 2>&1

# 实时查看日志 (PowerShell)
Get-Content debug.log -Wait
```

---

## 📊 性能优化建议

### 对于大文件 (>200MB)

1. **下采样**: 减小空间分辨率
   ```bash
   gdal_translate -outsize 50% 50% input.tif output.tif
   ```

2. **裁剪ROI**: 只保留关注区域
   ```bash
   gdalwarp -te xmin ymin xmax ymax input.tif output.tif
   ```

3. **压缩**: 使用LZW或DEFLATE压缩
   ```bash
   gdal_translate -co COMPRESS=LZW input.tif output_compressed.tif
   ```

### 对于MATLAB计算优化

编辑 `matlab/detectMiningDisturbance.m`，添加并行计算：
```matlab
% 启用并行计算
parpool('local', 4);  % 使用4核

% ... 你的代码 ...

% 关闭并行计算
delete(gcp('nocreate'));
```

---

## 📞 何时需要专业支持

如果你已尝试以上所有方案仍未解决，可能需要：

1. **MATLAB技术支持**: mathworks.com
2. **GDAL/GIS工具社区**: gdal.org, gis.stackexchange.com
3. **Python环保社区**: stackoverflow.com (tag: python + matplotlib + gdal)

请准备以下信息供专业人士参考：
- 完整的错误信息和堆栈跟踪
- 输入GeoTIFF文件的 `gdalinfo` 输出
- 系统配置 (Python版本、MATLAB版本、OS、内存)
- 后端完整日志输出

---

**祝你顺利排查问题！💪**
