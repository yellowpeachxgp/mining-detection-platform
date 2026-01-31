# 🔧 诊断工具和检查清单

## 📊 三种方式验证上传和处理

你有三种方式来验证文件是否成功上传和处理：

### 方式1️⃣: 浏览器开发者工具 (最直观)

**步骤**:
1. 打开网页 http://127.0.0.1:5000
2. 按 **F12** 打开开发者工具
3. 点击 **Console** 选项卡
4. 点击"运行检测"按钮
5. **在Console中观察日志**

**会看到**:
```
开始上传过程
NDVI文件: ndvi.tif (45.30MB)
Coal文件: coal.tif (23.15MB)
正在上传NDVI文件...
=== 开始上传 ndvi 文件 ===
文件名: ndvi.tif
文件大小: 45.30MB
✓ ndvi上传成功:
{job_id: "abc123-xxx", kind: "ndvi", path: "..."}
```

**查找关键词**:
- ✅ "✓ ndvi上传成功" = NDVI上传成功
- ✅ "✓ Coal上传成功" = 裸煤上传成功
- ✅ "✓ MATLAB检测完成" = 处理完成
- ❌ 任何"错误"或红色文本 = 问题

👉 **详细说明**: 查看 `DEBUG_GUIDE.md`

---

### 方式2️⃣: 后端日志 (最技术化)

**启动后端后，观察终端窗口**:

```
2026-01-31 10:15:25,123 - app - INFO - 上传成功: job_id=abc123, kind=ndvi
2026-01-31 10:15:30,456 - app - INFO - 上传成功: job_id=abc123, kind=coal
2026-01-31 10:15:31,123 - app - INFO - 开始MATLAB检测: job_id=abc123
2026-01-31 10:20:45,789 - app - INFO - MATLAB检测完成: job_id=abc123
```

**查找关键词**:
- "上传成功" = 文件上传成功
- "MATLAB检测完成" = 处理完成
- "ERROR" 或 "Exception" = 错误信息

---

### 方式3️⃣: 文件系统检查 (最可靠)

**打开资源管理器**:

1. 进入 `data/uploads/<job_id>/` 目录
   - 应该看到 `ndvi.tif` (30MB+)
   - 应该看到 `coal.tif` (15MB+)

2. 进入 `data/jobs/<job_id>/` 目录
   - MATLAB完成后，应该看到 7 个 .tif 文件
   - 每个文件都是 2-5 MB

**如果文件不存在**:
- 上传目录为空 → 上传失败
- 结果目录为空 → MATLAB未运行或失败

---

## 🛠️ 快速诊断脚本

### 使用 quick_diagnose.bat (推荐)

**Windows 用户**:
```bash
# 双击 quick_diagnose.bat
# 或在CMD中运行
quick_diagnose.bat
```

**功能**:
1. 自动检查后端是否运行
2. 自动创建必要的目录
3. 检查Python环境
4. 运行完整的诊断

**输出示例**:
```
[检查1] 后端服务连接...
✓ 后端服务运行正常

[检查2] 项目结构...
✓ data目录结构正常

[检查3] Python环境...
✓ Python环境正常

[检查4] 运行诊断脚本...
请输入NDVI GeoTIFF文件路径 (或直接回车使用示例): your_ndvi.tif
请输入裸煤概率GeoTIFF文件路径 (或直接回车使用示例): your_coal.tif
```

---

## 📋 完整诊断检查清单

逐项检查，找到问题所在：

### 🔍 启动前检查
- [ ] Python 3.8+ 已安装
- [ ] MATLAB R2020a+ 已安装
- [ ] `pip install -r requirements.txt` 已执行
- [ ] MATLAB引擎已配置 (如果遇到"No module matlab.engine"错误)

### 🚀 启动后检查
- [ ] `start.bat` 或 `python run_app.py` 已启动
- [ ] 终端显示 "Running on http://127.0.0.1:5000"
- [ ] 浏览器能打开 http://127.0.0.1:5000

### 📤 上传前检查
- [ ] NDVI.tif 文件存在本地
- [ ] coal.tif 文件存在本地
- [ ] 两个文件都有地理参考信息 (CRS)
- [ ] 文件大小合理 (< 500MB 推荐)

### ✅ 上传过程中检查
- [ ] 浏览器Console显示 "开始上传过程"
- [ ] Console显示 "✓ ndvi上传成功"
- [ ] Console显示 "✓ Coal上传成功"
- [ ] 文件出现在 `data/uploads/<job_id>/`

### 🔄 MATLAB处理中检查
- [ ] Console显示 "正在调用MATLAB detectMiningDisturbance函数"
- [ ] 后端日志显示 "开始MATLAB检测"
- [ ] 任务管理器显示 MATLAB.exe 进程在运行
- [ ] 内存使用在 1-3GB 之间

### 📊 处理完成后检查
- [ ] Console显示 "✓ MATLAB检测完成"
- [ ] 后端日志显示 "MATLAB检测完成"
- [ ] 结果出现在 `data/jobs/<job_id>/` (7个.tif文件)
- [ ] Console显示 "✅ 完成！"

### 🗺️ 地图显示检查
- [ ] 右侧地图加载完成 (能看到底图)
- [ ] 图层列表显示 5 个新图层
- [ ] 至少一个图层可见 (有彩色覆盖层)

### 🔍 交互查询检查
- [ ] 点击地图后，左侧显示坐标信息
- [ ] 左侧显示扰动年份和恢复年份
- [ ] 左侧显示 NDVI 时间序列曲线

---

## 🚨 快速故障排除

### 问题: 上传卡住了

**症状**: 显示"正在上传"超过30秒

**解决**:
```
1. 打开 F12 → Network 选项卡
2. 查看 POST /api/upload 请求是否还在进行
3. 如果是，说明:
   - 文件太大
   - 网络太慢
   - 后端无响应
4. 尝试:
   - 使用更小的文件
   - 重启后端
```

---

### 问题: MATLAB 处理超时

**症状**: 30分钟都还在"调用MATLAB"

**解决**:
```
1. 打开任务管理器
2. 查看是否有 MATLAB.exe 进程在运行
3. 如果有进程:
   - 等待 (大文件可能需要20-40分钟)
   - 或者关闭后端，使用更小的数据
4. 如果没有进程:
   - 后端可能崩溃了
   - 重启 start.bat
   - 查看后端日志中的错误
```

---

### 问题: 地图无图层显示

**症状**: 地图加载正常，但没有彩色覆盖层

**解决**:
```
1. 检查结果文件是否生成
   dir data\jobs\<job_id>\
   应该有7个.tif文件

2. 如果没有文件:
   - MATLAB处理失败
   - 查看后端日志找错误

3. 如果有文件:
   - 刷新页面 Ctrl+R
   - 打开 F12 查看Console是否有错误
   - 尝试更换浏览器
```

---

### 问题: "GeoTIFF 没有 CRS 信息"

**症状**: 点击地图时报错

**解决**:
```
使用GDAL工具添加CRS:
gdalwarp -s_srs EPSG:4326 input.tif output.tif

然后重新上传新的文件
```

---

## 📊 诊断工具文件列表

| 文件 | 功能 | 使用方式 |
|------|------|---------|
| `start.bat` | 启动后端 | 双击 |
| `quick_diagnose.bat` | 快速诊断 | 双击 (需要后端已启动) |
| `diagnostic_tool.py` | 完整诊断 | 由quick_diagnose.bat调用 |
| `DEBUG_GUIDE.md` | 调试指南 | 文本阅读 |

---

## 📞 收集信息用于支持

如果遇到无法解决的问题，收集以下信息：

1. **浏览器Console日志**
   ```
   F12 → Console → 全选 (Ctrl+A) → 复制 (Ctrl+C)
   ```

2. **后端日志**
   ```
   从 start.bat 窗口复制所有文本
   或从 app.log 文件中复制
   ```

3. **文件系统状态**
   ```
   dir data\uploads\
   dir data\jobs\
   gdalinfo ndvi.tif (前20行)
   ```

4. **系统信息**
   ```
   Python版本: E:\Anaconda\python.exe --version
   MATLAB版本: MATLAB 2024b (或其他版本)
   Windows版本: 在设置中查看
   ```

然后参考 `TROUBLESHOOTING.md` 中的对应错误进行排查。

---

**祝你诊断顺利！** 🔍

*最后更新: 2026-01-31*
