# 🚀 快速开始指南

## ⚡ 最快启动方式 (推荐)

### Windows 用户
1. **双击** `start.bat` 文件
2. 等待Python和依赖加载完成
3. 浏览器自动打开 http://127.0.0.1:5000

### Linux/Mac 用户
```bash
cd mining-platform
bash start.sh
```

---

## 📋 系统要求检查清单

在启动前，请确认以下内容已安装：

| 组件 | 版本 | 验证方法 |
|------|------|--------|
| **Python** | 3.8+ | `E:\Anaconda\python.exe --version` |
| **MATLAB** | R2020a+ | 检查MATLAB图标是否存在 |
| **Flask** | 3.0+ | `E:\Anaconda\python.exe -c "import flask; print(flask.__version__)"` |

### 📦 检查依赖是否安装

```bash
E:\Anaconda\python.exe -c "
import flask, numpy, rasterio, pyproj
print('✓ 所有核心依赖已安装')
"
```

如果提示缺少模块，自动安装：
```bash
cd mining-platform/backend
E:\Anaconda\python.exe -m pip install -r requirements.txt
```

### 🔧 检查MATLAB引擎是否可用

```bash
E:\Anaconda\python.exe -c "
import matlab.engine
print('✓ MATLAB引擎可用')
"
```

如果MATLAB引擎未安装，需要运行：
```bash
cd E:\Matlab2024b\extern\engines\python
E:\Anaconda\python.exe setup.py install
```

---

## 🎯 完整工作流程

### 步骤 1️⃣: 启动平台

**方式A (推荐):** 双击 `start.bat`

**方式B:** 手动启动
```bash
cd F:\挑战杯\mining-platform\backend
E:\Anaconda\python.exe run_app.py
```

### 步骤 2️⃣: 打开浏览器

访问 http://127.0.0.1:5000

你应该看到：
- 左侧：数据上传面板、图表、图层控制
- 右侧：交互式地图

### 步骤 3️⃣: 上传数据

1. 点击 **"NDVI 时序 GeoTIFF"** 输入框，选择你的 `ndvi.tif` 文件
2. 点击 **"裸煤概率 GeoTIFF"** 输入框，选择你的 `coal.tif` 文件
3. 确认 **"起始年份"** 字段（默认2010）

### 步骤 4️⃣: 运行检测

点击 **"▶️ 上传并运行检测"** 按钮

你将看到：
- ⏳ "上传 NDVI 文件..."
- ⏳ "上传裸煤概率文件..."
- ⏳ "调用 MATLAB 运行检测 (这可能需要一些时间)..."
- ⏳ "加载结果图层..."
- ✅ "完成！请点击地图查看..."

**等待时间:** 取决于文件大小，可能需要 1-10 分钟

### 步骤 5️⃣: 查看结果

地图上会显示彩色栅格图层：
- 🔴 **扰动年份** (默认显示) - 红色表示矿区被扰动的年份
- 🟢 **恢复年份** - 绿色表示恢复开始的年份
- 🟡 **潜在扰动区** - 黄色表示候选矿区
- 其他中间结果

### 步骤 6️⃣: 交互查询

在地图上 **点击任意位置**：
- 显示该像元的坐标
- 弹窗显示扰动年份和恢复年份
- 左侧图表显示 **NDVI 时间序列曲线**

---

## 🗂️ 文件说明

### 数据存储位置

```
mining-platform/
├── data/
│   ├── uploads/<job_id>/          # 上传的输入文件
│   │   ├── ndvi.tif
│   │   └── coal.tif
│   └── jobs/<job_id>/             # 检测结果输出
│       ├── mining_disturbance_mask.tif (核心)
│       ├── mining_disturbance_year.tif (核心)
│       ├── mining_recovery_year.tif (核心)
│       ├── potential_disturbance.tif
│       ├── res_disturbance_type.tif
│       ├── year_disturbance_raw.tif
│       └── year_recovery_raw.tif
```

### 结果文件说明

| 文件 | 含义 | 用途 |
|------|------|------|
| `mining_disturbance_mask.tif` | 矿区位置掩膜 (0/1) | **标记矿区位置** |
| `mining_disturbance_year.tif` | 扰动发生的年份 | **何时被扰动** |
| `mining_recovery_year.tif` | 恢复开始的年份 | **何时开始恢复** |
| `potential_disturbance.tif` | 潜在矿区标签 | 候选区域识别 |
| `res_disturbance_type.tif` | 扰动类型分类 | KNN分类结果 |
| `year_disturbance_raw.tif` | 原始扰动年份 | 未过滤的检测结果 |
| `year_recovery_raw.tif` | 原始恢复年份 | 未过滤的检测结果 |

---

## ⚠️ 常见问题

### Q1: "NameError: name 'matlab' is not defined"
**A:** MATLAB引擎未安装。运行：
```bash
cd E:\Matlab2024b\extern\engines\python
E:\Anaconda\python.exe setup.py install
```

### Q2: "GeoTIFF 没有 CRS 信息"
**A:** 你的GeoTIFF文件缺少地理坐标信息。需要用GDAL工具添加CRS：
```bash
# 使用gdal_translate添加地理参考
gdalwarp -s_srs EPSG:4326 input.tif output.tif
```

### Q3: "检测在运行中卡住了"
**A:**
- 可能文件太大，耐心等待
- 检查MATLAB是否在后台运行 (查看任务管理器)
- 查看浏览器开发者工具 (F12) 的Network选项卡

### Q4: "地图无法加载图层"
**A:**
1. 检查后端是否还在运行（终端窗口是否还开着）
2. 检查浏览器控制台错误 (F12 → Console)
3. 尝试刷新页面 (Ctrl+R)

### Q5: 如何导出结果
**A:** 结果保存在 `data/jobs/<job_id>/` 目录下，可以直接复制使用或在ArcGIS中打开。

---

## 🔧 调试技巧

### 查看后端日志
启动脚本后，终端会输出详细日志：
```
INFO:werkzeug: * Running on http://127.0.0.1:5000
INFO:app:上传成功: job_id=abc123, kind=ndvi
INFO:app:开始MATLAB检测: job_id=abc123, startyear=2010
INFO:app:MATLAB检测完成: job_id=abc123
```

### 查看浏览器控制台
按 **F12** 打开开发者工具：
- **Console** 选项卡：查看JavaScript错误
- **Network** 选项卡：查看API请求/响应
- **Storage** 选项卡：查看浏览器缓存

### 手动测试API

使用 `curl` 或 Postman 测试：
```bash
# 测试上传
curl -X POST http://127.0.0.1:5000/api/upload \
  -F "file=@ndvi.tif" \
  -F "kind=ndvi"

# 测试检测
curl -X POST http://127.0.0.1:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{"job_id":"abc123","startyear":2010}'

# 测试时间序列查询
curl "http://127.0.0.1:5000/api/ndvi-timeseries?job_id=abc123&lon=110.5&lat=35.5"
```

---

## 📞 获取帮助

如遇到问题：

1. **查看日志** - 后端终端输出有详细信息
2. **查看浏览器控制台** - F12 获取客户端错误
3. **检查数据格式** - 确保GeoTIFF有CRS信息
4. **重启服务** - 关闭 start.bat，重新启动

---

## ✅ 性能建议

- **文件大小**: 建议单个文件 < 500MB
- **内存**: 确保有 4GB+ 可用内存
- **处理时间**: 大文件可能需要 5-10 分钟
- **浏览器**: 推荐 Chrome / Firefox 最新版本

---

**祝你使用愉快！🎉**
