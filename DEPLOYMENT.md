# 采矿平台项目 - 部署完成检查清单

## ✅ 已完成的任务

### 1. 项目结构 ✓
```
mining-platform/
├── backend/
│   ├── app.py              # Flask后端应用
│   ├── config.py           # 配置文件（路径管理）
│   ├── matlab_runner.py    # MATLAB调用管理
│   ├── run_app.py          # 启动脚本
│   └── requirements.txt    # Python依赖
├── frontend/
│   ├── index.html          # 前端UI
│   ├── main.js             # ArcGIS Maps + Chart交互
│   └── style.css           # 样式
├── matlab/
│   ├── detectMiningDisturbance.m  # 主检测算法（输出7个TIF）
│   ├── creat_sample.m
│   ├── knn.m
│   ├── ljpl.m
│   ├── dtw.m
│   └── 其他辅助脚本
└── data/                   # 自动生成
    ├── uploads/            # 上传的输入文件
    └── jobs/               # 检测结果
```

### 2. Python环境 ✓
- **Python版本**: 3.12.7 (Anaconda)
- **已安装依赖**:
  - flask==3.0.0
  - flask-cors==4.0.0
  - numpy==1.26.4
  - rasterio==1.3.10
  - pyproj==3.6.1
- **MATLAB Engine**: 已安装 (E:\Matlab 2024b\Install)

### 3. MATLAB配置 ✓
- **MATLAB版本**: 2024b
- **安装位置**: E:\Matlab 2024b\Install
- **Python Engine**: 已集成

### 4. 后端服务 ✓
- **运行命令**: 
  ```powershell
  cd f:\挑战杯\mining-platform\backend
  E:\Anaconda\python.exe run_app.py
  ```
- **服务地址**: http://127.0.0.1:5000
- **状态**: 运行中

### 5. API端点已实现

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/upload` | POST | 上传NDVI和coal GeoTIFF文件 |
| `/api/run` | POST | 执行MATLAB检测 |
| `/api/ndvi-timeseries` | GET | 查询像元的NDVI时间序列和年份 |
| `/jobs/<job_id>/<filename>` | GET | 获取结果TIF文件 |
| `/` | GET | 前端页面 |

## 🚀 使用流程

### 步骤1: 启动后端
```powershell
cd f:\挑战杯\mining-platform\backend
E:\Anaconda\python.exe run_app.py
```
看到 `Running on http://127.0.0.1:5000` 即表示成功

### 步骤2: 打开浏览器
访问 http://127.0.0.1:5000

### 步骤3: 准备数据
1. 选择 NDVI 时序 GeoTIFF (多波段，每波段一个年份)
2. 选择 裸煤概率 GeoTIFF (多波段)
3. 输入起始年份（默认2010）

### 步骤4: 执行检测
点击"上传并运行检测"，系统将：
1. ✓ 上传NDVI文件
2. ✓ 上传coal文件  
3. ✓ 调用MATLAB的detectMiningDisturbance()
4. ✓ 自动生成7个结果TIF：
   - mining_disturbance_mask.tif - 核心: 矿区扰动掩膜
   - mining_disturbance_year.tif - 核心: 扰动年份
   - mining_recovery_year.tif - 核心: 恢复年份
   - potential_disturbance.tif - 中间结果
   - res_disturbance_type.tif - 中间结果
   - year_disturbance_raw.tif - 中间结果
   - year_recovery_raw.tif - 中间结果

### 步骤5: 查看结果
1. 图层自动加载到地图上（支持图层切换）
2. **点击地图像元**获取：
   - NDVI时间序列曲线（Chart.js）
   - 该像元的扰动和恢复年份
3. 弹窗显示像元信息

## 🔧 故障排除

### 问题1: MATLAB Engine未找到
**解决**: 已自动安装
```powershell
E:\Anaconda\python.exe -c "import matlab.engine; print('OK')"
```

### 问题2: 后端无法连接
检查：
- Flask是否运行中（看终端输出）
- 防火墙是否阻止端口5000
- 访问 http://127.0.0.1:5000

### 问题3: 检测结果为空
- 检查输入GeoTIFF的格式（需要标准GeoTIFF格式）
- 确认MATLAB中detectMiningDisturbance.m有CRS信息
- 查看后端日志获取详细错误

## 📊 项目输出

```
f:\挑战杯\mining-platform\data\jobs\<job_id>\
├── mining_disturbance_mask.tif          # 二值掩膜（0/1）
├── mining_disturbance_year.tif          # 扰动发生年份
├── mining_recovery_year.tif             # 恢复开始年份
├── potential_disturbance.tif            # 潜在扰动候选
├── res_disturbance_type.tif             # 扰动分类
├── year_disturbance_raw.tif             # 扰动年份原始值
└── year_recovery_raw.tif                # 恢复年份原始值
```

## 🎯 关键特性

✅ **实时地图可视化** - 基于ArcGIS API for JavaScript  
✅ **MATLAB集成** - Python调用MATLAB检测算法  
✅ **GeoTIFF支持** - 使用rasterio读取栅格数据  
✅ **交互式查询** - 点击地图查看NDVI曲线  
✅ **多波段处理** - 支持时间序列分析  
✅ **CORS跨域** - 支持前后端分离  

## 📝 注意事项

1. **Python路径**: 务必使用 `E:\Anaconda\python.exe` 而非其他Python版本
2. **MATLAB授权**: 确保MATLAB许可证有效（运行中可能需要交互授权）
3. **内存需求**: 处理大型GeoTIFF时需要足够的内存
4. **开发服务器**: 当前使用Flask内置服务器，生产环境需使用WSGI服务器

---
**项目状态**: ✅ 完全就绪  
**最后更新**: 2026-01-31  
**部署者**: GitHub Copilot
