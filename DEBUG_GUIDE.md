# 🔍 上传和处理过程调试指南

## 📝 如何检查上传是否成功

### 方法1: 浏览器开发者工具 (推荐 ⭐)

#### 步骤1: 打开开发者工具
1. 按 **F12** 打开浏览器开发者工具
2. 点击 **Console** 选项卡（控制台）

#### 步骤2: 上传文件并观察日志

你会看到以下日志输出序列：

```
开始上传过程
NDVI文件: ndvi.tif (45.30MB)
Coal文件: coal.tif (23.15MB)
正在上传NDVI文件...
=== 开始上传 ndvi 文件 ===
文件名: ndvi.tif
文件大小: 45.30MB
ndvi上传进度: 10%
ndvi上传进度: 25%
ndvi上传进度: 50%
ndvi上传进度: 75%
ndvi上传进度: 100%
上传耗时: 12.5秒
✓ ndvi上传成功:
{job_id: "abc123-def456", kind: "ndvi", path: "..."}
```

**关键词搜索** (按 Ctrl+F):
- ✅ **"✓ ndvi上传成功"** - NDVI文件上传成功
- ✅ **"✓ Coal上传成功"** - 裸煤文件上传成功
- ✅ **"✓ MATLAB检测完成"** - MATLAB处理完成
- ❌ **"✗"** 或 **"错误"** - 查找问题

#### 步骤3: 检查Network网络请求

1. 点击 **Network** 选项卡
2. 点击"运行检测"按钮
3. 查看网络请求列表：

```
POST /api/upload          200  ✓ (上传NDVI)
POST /api/upload          200  ✓ (上传Coal)
POST /api/run            200  ✓ (启动MATLAB)
GET  /jobs/abc123/...    200  ✓ (获取结果文件)
```

**如果有红色请求** (状态码 400/500):
- 点击请求行
- 查看 **Response** 选项卡，看错误信息
- 记录错误信息用于故障排除

---

### 方法2: 后端日志文件

#### Windows用户

启动 `start.bat` 后，后端窗口会输出详细日志：

```
2026-01-31 10:15:23,456 - app - INFO - UPLOAD_DIR: F:\挑战杯\mining-platform\data\uploads
2026-01-31 10:15:23,456 - app - INFO - JOB_DIR: F:\挑战杯\mining-platform\data\jobs
2026-01-31 10:15:25,123 - app - INFO - 上传成功: job_id=abc123, kind=ndvi, path=...
2026-01-31 10:15:30,456 - app - INFO - 上传成功: job_id=abc123, kind=coal, path=...
2026-01-31 10:15:31,123 - app - INFO - 开始MATLAB检测: job_id=abc123, startyear=2010
2026-01-31 10:20:45,789 - app - INFO - MATLAB检测完成: job_id=abc123
2026-01-31 10:20:46,012 - app - INFO - 获取结果文件: abc123/mining_disturbance_year.tif
```

**关键词搜索**:
- "上传成功" - 文件上传成功
- "开始MATLAB检测" - MATLAB开始处理
- "MATLAB检测完成" - MATLAB处理完成
- "ERROR" 或 "Exception" - 错误信息

#### Linux/Mac用户

将日志重定向到文件：
```bash
cd mining-platform/backend
python3 run_app.py 2>&1 | tee app.log

# 在另一个终端查看实时日志
tail -f app.log
```

---

### 方法3: 文件系统验证

#### 检查上传目录

```bash
# Windows (在CMD中)
dir data\uploads\<job_id>\

# Linux/Mac
ls -lh data/uploads/<job_id>/
```

应该看到：
```
ndvi.tif   (大小: 45MB+)
coal.tif   (大小: 20MB+)
```

如果文件不存在，说明上传失败。

#### 检查结果目录

```bash
# Windows
dir data\jobs\<job_id>\

# Linux/Mac
ls -lh data/jobs/<job_id>/
```

MATLAB处理完成后，应该看到 7 个 .tif 文件：
```
mining_disturbance_mask.tif       (2MB+)  ✓ 核心
mining_disturbance_year.tif       (2MB+)  ✓ 核心
mining_recovery_year.tif          (2MB+)  ✓ 核心
potential_disturbance.tif         (2MB+)  中间
res_disturbance_type.tif          (2MB+)  中间
year_disturbance_raw.tif          (2MB+)  中间
year_recovery_raw.tif             (2MB+)  中间
```

如果缺少这些文件，MATLAB处理可能失败。

---

## 🔄 完整的上传和处理流程跟踪

### 时间表示例

假设你在 **10:15:00** 点击"运行检测"：

```
时间          事件                              位置
────────────────────────────────────────────────────────────────────
10:15:00      点击"运行检测"                    浏览器
10:15:02      ⏳ 上传NDVI文件                    前端状态栏
10:15:05      ✓ NDVI上传成功                    浏览器Console
              ⏳ 上传Coal文件                   前端状态栏
10:15:10      ✓ Coal上传成功                    浏览器Console
              ⏳ 调用MATLAB运行检测             前端状态栏
              开始MATLAB检测                    后端日志
10:15:15      - MATLAB数据加载中 -              (无外部反馈)
10:15:30      - MATLAB处理中 -                  (无外部反馈)
10:20:45      ✓ MATLAB检测完成                  后端日志 + 浏览器
              ⏳ 加载结果图层                   前端状态栏
10:20:47      ✓ 完成！请点击地图...             前端状态栏
              地图显示结果图层                  右侧地图
```

**关键时间段**:
- 上传: 几秒到几十秒 (取决于文件大小和网络)
- MATLAB处理: 1-10分钟 (取决于数据大小)
- 地图加载: <1秒

---

## ⚠️ 常见问题症状和诊断

### 症状1: "一直在上传..."

**原因**: 上传卡住或网络问题

**诊断**:
1. 打开 F12 → Network
2. 查看 POST /api/upload 请求是否还在进行
3. 如果状态是 "pending" 超过30秒，说明：
   - 文件太大
   - 网络连接不稳定
   - 后端无响应

**解决方案**:
- 使用较小的文件测试
- 检查网络连接
- 重启后端

### 症状2: "显示上传成功，但MATLAB没有开始"

**原因**: 可能是以下几种:
1. Coal文件上传失败
2. MATLAB引擎未启动
3. 文件格式问题

**诊断**:
```javascript
// 在 Console 中输入以下代码检查job_id是否正确
console.log(jobId)  // 应该显示 "abc123-xxx" 格式的ID
```

查看后端日志是否有：
- "开始MATLAB检测"
- "MATLAB引擎启动失败"
- "文件不存在"

### 症状3: "MATLAB运行超过10分钟还未完成"

**原因**:
1. 文件太大，MATLAB处理耗时
2. MATLAB进程卡死
3. 内存不足

**诊断**:
1. 打开任务管理器 (Ctrl+Shift+Esc)
2. 查看是否有 "MATLAB.exe" 或 "python.exe" 进程在运行
3. 查看内存使用 (应该在 500MB-2GB)

**解决方案**:
- 等待 20 分钟以上 (大文件可能需要很长时间)
- 如果进程停止，重启后端
- 使用更小的数据集测试

### 症状4: "地图显示了，但没有结果图层"

**原因**: 结果文件生成失败或API返回错误

**诊断**:
```javascript
// 在 Console 中查看runRes对象
console.log(runRes)  // 应该显示7个输出文件URL
```

检查文件系统：
```bash
ls data/jobs/<job_id>/
# 应该有7个.tif文件
```

**解决方案**:
- 查看后端日志，找到 "ERROR" 信息
- 检查GeoTIFF文件格式是否正确
- 参考 TROUBLESHOOTING.md

---

## 🛠️ 高级调试技巧

### 1. 保存Console日志

```javascript
// 在浏览器Console中执行，保存所有日志到文件
const logs = document.body.innerText;
const blob = new Blob([logs], {type: 'text/plain'});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'debug_log.txt';
a.click();
```

### 2. 检查API响应数据

```javascript
// 在运行detect后，查看完整的响应数据
fetch('/api/run', {...}).then(r => r.json()).then(d => {
  console.table(d.outputs)  // 以表格形式显示输出文件
})
```

### 3. 验证上传的文件

```bash
# 使用GDAL工具检查上传的NDVI文件是否有效
gdalinfo data/uploads/<job_id>/ndvi.tif | head -20

# 应该看到:
# - Coordinate System: EPSG:XXXX
# - Size: XXXX x YYYY
# - Band count: 34 (或其他数字)
```

### 4. 跟踪MATLAB执行

在 `backend/matlab_runner.py` 中，查看日志记录：

```python
logger.info(f"MATLAB参数:")
logger.info(f"  MATLAB目录: {matlab_dir}")
logger.info(f"  NDVI路径: {ndvi_path}")
logger.info(f"  裸煤路径: {coal_path}")
logger.info(f"  输出目录: {out_dir}")
logger.info(f"  起始年份: {startyear}")
logger.info("调用MATLAB函数: detectMiningDisturbance()")
logger.info("MATLAB函数执行成功")
```

---

## 📊 性能监控

### 内存使用

```bash
# Windows (PowerShell)
while($true) {
  ps python | select Name, WorkingSet | Format-Table -AutoSize
  Start-Sleep -Seconds 5
}

# Linux/Mac
while true; do ps aux | grep python; sleep 5; done
```

### 磁盘空间

```bash
# 监控data目录大小
du -sh data/

# 监控uploads目录大小
du -sh data/uploads/

# 监控jobs目录大小
du -sh data/jobs/
```

---

## 📋 调试检查清单

上传文件时，逐项检查：

- [ ] 浏览器Console显示 "开始上传过程"
- [ ] 后端日志显示 "上传成功: job_id=xxx"
- [ ] 文件存在于 `data/uploads/<job_id>/`
- [ ] 浏览器Console显示 "✓ MATLAB检测完成"
- [ ] 后端日志显示 "MATLAB检测完成: job_id=xxx"
- [ ] 结果文件存在于 `data/jobs/<job_id>/`
- [ ] 地图上显示结果图层
- [ ] 点击地图可以查看NDVI曲线

如果某一步失败，对应的错误信息会在Console或后端日志中显示。

---

## 📞 获取帮助

如果遇到问题，请收集：

1. **浏览器Console的完整日志** (F12 → Console → 全选复制)
2. **后端终端的完整日志** (start.bat窗口的所有输出)
3. **文件系统状态** (运行 `dir data` 显示目录结构)
4. **错误信息** (完整的错误信息，包括行号)

然后参考 `TROUBLESHOOTING.md` 进行故障排除。

---

**祝你调试顺利！🔍**

*最后更新: 2026-01-31*
