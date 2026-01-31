# 🚨 MATLAB处理问题 - 快速诊断指南

## 📌 现在的情况

你上传的文件：
```
ndvi.tif:  2.0 GB   ⚠️ 非常大！
coal.tif:  23 MB
```

**输出目录是空的** → MATLAB没有生成结果

---

## 🔍 立即检查 (5分钟)

### 步骤1: 停止后端

在 start.bat 窗口按 **Ctrl+C** 停止服务

### 步骤2: 测试MATLAB引擎

```bash
# 打开CMD或PowerShell，进入项目目录
cd F:\挑战杯\mining-platform

# 运行这个命令
python test_matlab.py
```

**预期输出：**
```
✓ MATLAB.engine module found
✓ MATLAB engine started successfully
✓ MATLAB version: ...
✓ MATLAB engine is working correctly!
```

**如果显示错误：**
```
✗ MATLAB.engine not found
```
→ 说明MATLAB引擎没有安装，需要运行：
```
cd E:\Matlab2024b\extern\engines\python
python setup.py install
```

### 步骤3: 查看后端错误日志

重新启动后端，看是否有错误信息：

```bash
# 启动后端并记录日志
python backend\run_app.py > backend.log 2>&1

# 在另一个CMD查看日志
type backend.log
```

---

## ⚡ 可能的原因

### 原因1: MATLAB引擎未安装
**症状**: 看到 "ModuleNotFoundError: No module named 'matlab.engine'"

**解决**:
```
cd E:\Matlab2024b\extern\engines\python
python setup.py install
```

### 原因2: MATLAB引擎启动失败
**症状**: 后端日志显示 "Error: Could not find MATLAB installation"

**解决**:
- 检查MATLAB是否已安装
- 重启电脑
- 确保MATLAB许可证有效

### 原因3: 文件太大，处理时间太长
**症状**: MATLAB还在处理，进程占用CPU/内存

**当前**:
- NDVI文件: 2.0 GB (超大)
- 预计处理时间: **1-2 小时或更长**

**解决**:
- 继续等待
- 或者用更小的文件测试

### 原因4: 输入文件格式错误
**症状**: MATLAB接收到文件但处理失败，没有生成输出

**检查**:
```bash
# 检查文件是否有地理参考信息
gdalinfo ndvi.tif | head -20
gdalinfo coal.tif | head -20

# 应该看到 "COORDINATE_SYSTEM" 或 "CRS"
```

---

## 🛠️ 立即排查步骤

### 方案A: 快速测试 (用小文件)

```
1. 用一个小的GeoTIFF文件测试 (< 50MB)
2. 看MATLAB是否能处理
3. 如果能处理小文件，说明MATLAB正常
4. 2GB文件只是需要很长时间
```

### 方案B: 完整诊断

```
1. 运行 python test_matlab.py
2. 检查后端日志
3. 查看任务管理器中MATLAB进程
4. 耐心等待更长的时间
```

### 方案C: 重置并重新开始

```
1. 停止后端 (Ctrl+C)
2. 删除 data 目录
3. 重新启动后端
4. 用更小的文件上传和处理
5. 完成后再试大文件
```

---

## 📋 我需要你做的

**请告诉我以下信息：**

1. **后端窗口显示的最后一条消息是什么？**
   (复制粘贴后端窗口的文本)

2. **任务管理器中看到这些进程吗？**
   - [ ] python.exe
   - [ ] MATLAB.exe

3. **运行 `python test_matlab.py` 的输出是什么？**

4. **NDVI.tif 和 coal.tif 是从哪里来的？**
   (自己生成的还是别人给的？)

有了这些信息，我能更准确地诊断问题。

---

## 🎯 最可能的原因排序

1. **最可能** (60%)
   - MATLAB引擎未安装
   - 需要运行: `cd E:\Matlab2024b\extern\engines\python && python setup.py install`

2. **次可能** (25%)
   - MATLAB还在处理2GB文件
   - 需要等待1-2小时

3. **不太可能** (10%)
   - 文件格式有问题
   - 需要检查GeoTIFF是否有CRS

4. **很少见** (5%)
   - MATLAB许可证问题
   - 系统内存不足

---

## 🚨 如果还是不行

保存以下信息并告诉我：

1. `test_matlab.py` 的完整输出
2. `start.bat` 窗口的最后50行日志
3. 任务管理器的截图 (显示MATLAB和python进程)
4. `dir data\` 的输出

这样我能给你更具体的解决方案。

---

**现在立即开始检查！** ⏱️
