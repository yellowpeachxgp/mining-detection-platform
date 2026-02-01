# 露天矿区扰动检测平台

基于 KNN-DTW 时序分类算法的矿区生态扰动与恢复检测系统。

## 功能特性

- **智能检测**: KNN-DTW 算法分析 NDVI 时序数据，自动识别矿区扰动
- **年份定位**: 精确定位扰动发生年份和恢复开始年份
- **地图可视化**: ArcGIS Maps SDK 集成，支持结果图层叠加与交互查询
- **用户系统**: JWT 认证、角色权限管理、任务历史记录
- **动态瓦片**: 实时渲染 GeoTIFF 结果为地图瓦片

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite 5 + ArcGIS Maps SDK 4.29 + Chart.js |
| 后端 | Flask 3.0 + SQLAlchemy + JWT |
| 算法 | Python (Numba JIT 加速) — 原 MATLAB 算法已完整重构 |
| 数据 | SQLite + GeoTIFF |

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
python app.py
```

服务启动于 http://127.0.0.1:5001

### 前端

```bash
cd frontend
npm install
npm run dev
```

开发服务器启动于 http://127.0.0.1:5173

## 项目结构

```
mining-detection-platform/
├── backend/
│   ├── app.py                 # Flask 应用入口
│   ├── models.py              # SQLAlchemy 数据模型
│   ├── auth.py                # JWT 认证逻辑
│   ├── routes/                # API 路由蓝图
│   │   ├── auth_routes.py     # 认证接口
│   │   ├── job_routes.py      # 任务接口
│   │   ├── tile_routes.py     # 瓦片服务
│   │   └── admin_routes.py    # 管理接口
│   ├── runners/
│   │   └── algorithm/         # KNN-DTW 算法实现
│   │       ├── dtw.py         # 动态时间规整
│   │       ├── knn_dtw.py     # KNN 分类器
│   │       ├── bwlvbo.py      # 时序平滑
│   │       └── sample_generator.py  # 模板生成
│   ├── services/              # 业务服务层
│   └── tests/                 # 测试套件
├── frontend/
│   └── src/
│       ├── pages/             # 页面组件
│       ├── components/        # 通用组件
│       └── store/             # Zustand 状态管理
├── docs/                      # 技术文档
└── matlab/                    # 原始 MATLAB 代码 (参考)
```

## 文档

| 文档 | 说明 |
|------|------|
| [技术文档](docs/TECHNICAL_DOCUMENTATION.md) | 完整技术实现细节 |
| [API 文档](docs/API.md) | RESTful 接口说明 |
| [架构文档](docs/ARCHITECTURE.md) | 系统架构设计 |
| [数据库文档](docs/DATABASE.md) | 数据模型设计 |
| [部署指南](docs/DEPLOYMENT.md) | 生产环境部署 |
| [用户指南](docs/USER_GUIDE.md) | 使用说明 |
| [技术图表](docs/DIAGRAMS.md) | Mermaid 图表集 |

## 核心算法

系统使用 **KNN-DTW (K-近邻 + 动态时间规整)** 算法对 NDVI 时序进行分类：

1. **预处理**: 数据清洗、归一化、计算百分位边界
2. **模板生成**: 生成 49 个典型 NDVI 变化模板 (扰动/恢复/稳定)
3. **DTW 匹配**: 计算每个像元与模板的 DTW 距离
4. **分类决策**: 选择最近邻模板，提取扰动/恢复年份
5. **空间滤波**: 形态学开运算去除噪声
6. **裸煤验证**: 结合裸煤概率数据过滤误检

算法使用 Numba JIT 编译加速，性能提升 50-100 倍。

## 输出结果

| 文件 | 说明 |
|------|------|
| `mining_disturbance_mask.tif` | 扰动区域二值掩膜 |
| `mining_disturbance_year.tif` | 扰动发生年份 |
| `mining_recovery_year.tif` | 恢复开始年份 |
| `potential_disturbance.tif` | 潜在扰动连通区标记 |
| `res_disturbance_type.tif` | 扰动类型分类 (1-49) |

## 测试

```bash
cd backend
python -m pytest tests/ -v
```

包含 19 个测试用例，覆盖 DTW、BWlvbo、模板生成、KNN 分类等核心模块。

## 许可证

MIT License

---

**版本**: 1.0.0
**更新**: 2026-02-01
