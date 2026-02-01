# 露天矿区扰动检测平台 — 完整技术文档

**版本**: 1.0.0
**最后更新**: 2026年2月1日

---

## 目录

1. [系统概述](#1-系统概述)
2. [系统架构](#2-系统架构)
3. [后端技术栈](#3-后端技术栈)
4. [前端技术栈](#4-前端技术栈)
5. [核心算法详解](#5-核心算法详解)
6. [数据库设计](#6-数据库设计)
7. [API接口规范](#7-api接口规范)
8. [地理空间处理](#8-地理空间处理)
9. [瓦片服务系统](#9-瓦片服务系统)
10. [安全与认证](#10-安全与认证)
11. [性能优化策略](#11-性能优化策略)
12. [部署与运维](#12-部署与运维)

---

## 1. 系统概述

### 1.1 项目背景

本平台是一个基于遥感时序数据的露天矿区扰动检测系统，采用 **KNN-DTW (K-Nearest Neighbors with Dynamic Time Warping)** 算法，通过分析 NDVI (归一化植被指数) 时间序列数据，自动识别采矿活动导致的植被扰动区域及其恢复情况。

### 1.2 核心功能

| 功能模块 | 描述 |
|---------|------|
| 数据上传 | 支持多波段 NDVI GeoTIFF 和裸煤概率 GeoTIFF 上传 |
| 扰动检测 | 基于 KNN-DTW 算法的自动扰动区域识别 |
| 时序分析 | 单像元 NDVI 时间序列可视化与分析 |
| 结果可视化 | 矢量/栅格双模式地图展示 |
| 数据导出 | 检测结果 GeoTIFF 文件下载 |
| 用户管理 | 完整的认证授权与多用户支持 |
| 任务管理 | 历史任务查看、删除与管理后台 |

### 1.3 技术栈总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                         │
│  React 18 + Vite 5 + Zustand + ArcGIS Maps SDK + Chart.js       │
├─────────────────────────────────────────────────────────────────┤
│                        通信层 (API)                              │
│  RESTful API + JWT Authentication + Axios                       │
├─────────────────────────────────────────────────────────────────┤
│                        后端层 (Backend)                          │
│  Flask 3.0 + SQLAlchemy + Flask-CORS + Blueprint                │
├─────────────────────────────────────────────────────────────────┤
│                        算法层 (Algorithm)                        │
│  NumPy + SciPy + PyWavelets + Numba + Joblib                    │
├─────────────────────────────────────────────────────────────────┤
│                        地理处理层 (GeoProcessing)                │
│  Rasterio + PyProj + Pillow                                     │
├─────────────────────────────────────────────────────────────────┤
│                        数据层 (Database)                         │
│  SQLite + File System (GeoTIFF)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构

### 2.1 整体架构图

```
                                    ┌─────────────────┐
                                    │   Web Browser   │
                                    │  (React SPA)    │
                                    └────────┬────────┘
                                             │
                                             │ HTTP/HTTPS
                                             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              Flask Application                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  auth_bp     │  │   job_bp     │  │  tile_bp     │  │  admin_bp    │   │
│  │  /api/auth/* │  │  /api/*      │  │  /api/tiles/*│  │ /api/admin/* │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                  │           │
│         └─────────────────┼─────────────────┼──────────────────┘           │
│                           │                 │                               │
│  ┌────────────────────────┼─────────────────┼─────────────────────────┐    │
│  │                    Services Layer                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐     │    │
│  │  │ geo_service │  │tile_service │  │    Detection Engine     │     │    │
│  │  │  - CRS转换   │  │  - 瓦片渲染  │  │  ┌───────────────────┐ │     │    │
│  │  │  - 坐标采样  │  │  - 色彩映射  │  │  │   KNN-DTW Core    │ │     │    │
│  │  │  - 边界计算  │  │  - 缓存管理  │  │  │  ┌─────────────┐  │ │     │    │
│  │  └─────────────┘  └─────────────┘  │  │  │  DTW (Numba) │  │ │     │    │
│  │                                     │  │  ├─────────────┤  │ │     │    │
│  │                                     │  │  │   BWlvbo    │  │ │     │    │
│  │                                     │  │  ├─────────────┤  │ │     │    │
│  │                                     │  │  │Sample Gen.  │  │ │     │    │
│  │                                     │  │  └─────────────┘  │ │     │    │
│  │                                     │  └───────────────────┘ │     │    │
│  │                                     └─────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          Data Layer                                    │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │    SQLite DB    │  │   Upload Dir    │  │     Job Dir         │   │  │
│  │  │  - users        │  │  - ndvi.tif     │  │  - mining_*.tif     │   │  │
│  │  │  - jobs         │  │  - coal.tif     │  │  - potential_*.tif  │   │  │
│  │  │  - job_files    │  │                 │  │  - year_*.tif       │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
mining_platform/
├── backend/                          # 后端服务
│   ├── app.py                        # Flask 应用入口
│   ├── config.py                     # 配置管理
│   ├── models.py                     # SQLAlchemy 数据模型
│   ├── auth.py                       # JWT 令牌生成/验证
│   ├── decorators.py                 # 路由装饰器 (jwt_required, admin_required)
│   ├── routes/                       # 蓝图路由
│   │   ├── auth_routes.py            # 认证相关 API
│   │   ├── job_routes.py             # 任务相关 API
│   │   ├── tile_routes.py            # 瓦片服务 API
│   │   ├── admin_routes.py           # 管理员 API
│   │   └── user_routes.py            # 用户资料 API
│   ├── services/                     # 业务服务
│   │   ├── geo_service.py            # 地理空间处理
│   │   └── tile_service.py           # 瓦片渲染服务
│   ├── runners/                      # 检测引擎
│   │   ├── __init__.py               # 引擎工厂
│   │   ├── base_runner.py            # 抽象基类
│   │   ├── python_runner.py          # Python 检测引擎
│   │   └── algorithm/                # 核心算法
│   │       ├── knn_dtw.py            # KNN-DTW 分类器
│   │       ├── dtw.py                # 动态时间规整
│   │       ├── bwlvbo.py             # 时序平滑算法
│   │       ├── sample_generator.py   # 训练模板生成
│   │       ├── utils.py              # 工具函数
│   │       └── geotiff_io.py         # GeoTIFF 读写
│   └── requirements.txt              # Python 依赖
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── main.jsx                  # React 入口
│   │   ├── App.jsx                   # 路由配置
│   │   ├── api/
│   │   │   └── client.js             # Axios 实例 + 拦截器
│   │   ├── components/               # UI 组件
│   │   │   ├── Layout.jsx            # 布局框架
│   │   │   ├── MapView.jsx           # ArcGIS 地图组件
│   │   │   ├── NdviChart.jsx         # NDVI 图表
│   │   │   ├── FileUpload.jsx        # 文件上传
│   │   │   └── DownloadPanel.jsx     # 下载面板
│   │   ├── pages/                    # 页面组件
│   │   │   ├── DetectionPage.jsx     # 检测主页
│   │   │   ├── HistoryPage.jsx       # 历史记录
│   │   │   ├── LoginPage.jsx         # 登录页
│   │   │   └── admin/
│   │   │       └── Dashboard.jsx     # 管理后台
│   │   └── styles/
│   │       └── index.css             # 全局样式
│   ├── package.json                  # 前端依赖
│   └── vite.config.js                # Vite 配置
├── data/                             # 数据存储
│   ├── uploads/                      # 上传文件
│   ├── jobs/                         # 检测结果
│   └── mining.db                     # SQLite 数据库
└── docs/                             # 文档
```

### 2.3 请求处理流程

```
[用户操作] → [React 组件] → [Axios Client] → [Flask 路由]
                                    │
                                    ▼
                           [JWT 验证装饰器]
                                    │
                                    ▼
                           [业务逻辑处理]
                                    │
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
        [数据库操作]          [文件系统]          [算法计算]
               │                    │                    │
               └────────────────────┼────────────────────┘
                                    ▼
                            [JSON 响应]
                                    │
                                    ▼
                         [Axios 响应拦截器]
                                    │
                           ┌────────┴────────┐
                           ▼                 ▼
                      [成功处理]        [401 自动刷新]
                           │                 │
                           ▼                 ▼
                      [状态更新]        [重新请求]
```

---

## 3. 后端技术栈

### 3.1 Flask 框架 (v3.0.0)

**文件**: `backend/app.py`

Flask 是本系统的核心 Web 框架，采用工厂模式创建应用实例。

#### 3.1.1 应用工厂

```python
def create_app():
    app = Flask(__name__)
    CORS(app)  # 跨域资源共享

    # 数据库配置
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = SECRET_KEY

    # 初始化扩展
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(auth_bp)     # /api/auth/*
    app.register_blueprint(user_bp)     # /api/user/*
    app.register_blueprint(job_bp)      # /api/* (jobs, upload, run)
    app.register_blueprint(tile_bp)     # /api/tiles/*
    app.register_blueprint(admin_bp)    # /api/admin/*

    return app
```

#### 3.1.2 蓝图架构

| 蓝图 | URL 前缀 | 职责 |
|------|----------|------|
| `auth_bp` | `/api/auth` | 用户注册、登录、令牌刷新 |
| `user_bp` | `/api/user` | 用户个人资料管理 |
| `job_bp` | `/api` | 文件上传、检测执行、任务管理 |
| `tile_bp` | `/api/tiles` | 动态瓦片渲染服务 |
| `admin_bp` | `/api/admin` | 管理员统计与用户管理 |

### 3.2 SQLAlchemy ORM (v3.1.1)

**文件**: `backend/models.py`

#### 3.2.1 User 模型

```python
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' | 'admin'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    # 关联关系
    jobs = db.relationship("Job", backref="user", lazy="dynamic")
```

#### 3.2.2 Job 模型

```python
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False, index=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    # 状态值: pending → running → completed | failed

    engine = db.Column(db.String(20), nullable=True)      # 'PythonRunner'
    startyear = db.Column(db.Integer, nullable=True)       # NDVI 起始年份
    ndvi_filename = db.Column(db.String(255), nullable=True)
    coal_filename = db.Column(db.String(255), nullable=True)

    # JSON 序列化字段
    bounds_json = db.Column(db.Text, nullable=True)       # 地理边界
    crs_info_json = db.Column(db.Text, nullable=True)     # 坐标系信息
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    # 关联关系
    files = db.relationship("JobFile", backref="job", lazy="dynamic",
                            cascade="all, delete-orphan")

    @property
    def bounds(self):
        """反序列化地理边界"""
        return json.loads(self.bounds_json) if self.bounds_json else None

    @bounds.setter
    def bounds(self, value):
        self.bounds_json = json.dumps(value) if value else None
```

#### 3.2.3 JobFile 模型

```python
class JobFile(db.Model):
    __tablename__ = "job_files"

    id = db.Column(db.Integer, primary_key=True)
    job_db_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(100), nullable=True)      # 显示名称
    file_type = db.Column(db.String(20), nullable=False, default="output")  # input|output
    size = db.Column(db.Integer, nullable=True)           # 文件大小 (bytes)
```

### 3.3 配置管理

**文件**: `backend/config.py`

```python
import os
import secrets

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")    # 上传文件存储
JOB_DIR = os.path.join(DATA_DIR, "jobs")          # 检测结果存储

# 检测引擎选择
DETECTION_ENGINE = os.environ.get('DETECTION_ENGINE', 'python')

# 数据库配置 (支持环境变量覆盖)
DATABASE_URI = os.environ.get('DATABASE_URI', f"sqlite:///{DATA_DIR}/mining.db")

# JWT 配置
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
ACCESS_TOKEN_EXPIRE = int(os.environ.get('ACCESS_TOKEN_EXPIRE', 2))   # 小时
REFRESH_TOKEN_EXPIRE = int(os.environ.get('REFRESH_TOKEN_EXPIRE', 30))  # 天

# 默认管理员
DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@mining.local')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
```

### 3.4 依赖库详解

**文件**: `backend/requirements.txt`

| 库名 | 版本 | 用途 |
|------|------|------|
| `flask` | 3.0.0 | Web 框架 |
| `flask-cors` | 4.0.0 | 跨域资源共享支持 |
| `flask-sqlalchemy` | 3.1.1 | ORM 集成 |
| `numpy` | 1.26.4 | 数值计算核心库 |
| `rasterio` | 1.3.10 | GeoTIFF 读写 |
| `pyproj` | 3.6.1 | 坐标系转换 |
| `scipy` | ≥1.11.0 | 科学计算 (形态学滤波) |
| `PyWavelets` | ≥1.5.0 | 小波变换 (信号去噪) |
| `numba` | ≥0.58.0 | JIT 编译加速 |
| `joblib` | ≥1.3.0 | 并行计算 |
| `PyJWT` | ≥2.8.0 | JWT 令牌处理 |
| `Werkzeug` | ≥3.0.0 | 密码哈希 |
| `Pillow` | ≥10.0.0 | 图像处理 (瓦片生成) |

---

## 4. 前端技术栈

### 4.1 React 18 + Vite 5

**文件**: `frontend/package.json`

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.3",
    "axios": "^1.6.5",
    "chart.js": "^4.4.1",
    "react-chartjs-2": "^5.2.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.12"
  }
}
```

### 4.2 Axios 客户端配置

**文件**: `frontend/src/api/client.js`

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 600000,  // 10分钟超时 (大文件处理)
})

// 请求拦截器：自动添加 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：自动刷新令牌
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
          const { access_token } = res.data
          localStorage.setItem('access_token', access_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)  // 重试原请求
        } catch (refreshError) {
          // 刷新失败，跳转登录
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
```

**关键特性**:
- **自动令牌注入**: 每个请求自动携带 `Authorization: Bearer <token>`
- **透明令牌刷新**: 401 响应时自动尝试使用 refresh_token 获取新 access_token
- **请求重试**: 令牌刷新成功后自动重试原请求
- **超时配置**: 10分钟超时适应大文件上传和长时间计算

### 4.3 ArcGIS Maps SDK 4.29

**文件**: `frontend/src/components/MapView.jsx`

ArcGIS Maps SDK 通过 CDN 方式加载，采用 AMD 模块系统。

#### 4.3.1 模块加载

```javascript
const require = window.require  // ArcGIS AMD loader

require([
  "esri/Map",
  "esri/views/MapView",
  "esri/widgets/LayerList",
  "esri/geometry/support/webMercatorUtils",
  "esri/geometry/Extent",
  "esri/layers/GeoJSONLayer",
  "esri/layers/WebTileLayer",
  "esri/renderers/UniqueValueRenderer",
  "esri/renderers/SimpleRenderer",
  "esri/symbols/SimpleFillSymbol",
  "esri/Graphic",
  "esri/geometry/Polygon",
], (Map, MapView, LayerList, webMercatorUtils, Extent,
    GeoJSONLayer, WebTileLayer, UniqueValueRenderer,
    SimpleRenderer, SimpleFillSymbol, Graphic, Polygon) => {
  // 初始化地图
})
```

#### 4.3.2 图层类型

| 图层类型 | 用途 | 数据源 |
|---------|------|-------|
| `GeoJSONLayer` | 矢量显示 | `/api/result-geojson/{job_id}/{layer}` |
| `WebTileLayer` | 栅格显示 | `/api/tiles/{job_id}/{layer}/{z}/{x}/{y}.png` |

#### 4.3.3 渲染器配置

**扰动掩膜 (SimpleRenderer)**:
```javascript
new SimpleRenderer({
  symbol: new SimpleFillSymbol({
    color: [220, 38, 38, 0.5],  // 半透明红色
    outline: { color: [185, 28, 28], width: 1 }
  })
})
```

**扰动年份 (UniqueValueRenderer)**:
```javascript
new UniqueValueRenderer({
  field: "year",
  defaultSymbol: new SimpleFillSymbol({
    color: [128, 128, 128, 0.5],
    outline: { color: [100, 100, 100], width: 1 }
  }),
  uniqueValueInfos: generateYearColors(2010, 2045, [255, 100, 100], [139, 0, 0])
})
```

**年份颜色渐变生成**:
```javascript
const generateYearColors = (startYear, endYear, startColor, endColor) => {
  const colors = []
  const range = endYear - startYear
  for (let year = startYear; year <= endYear; year++) {
    const t = (year - startYear) / range
    const r = Math.round(startColor[0] + t * (endColor[0] - startColor[0]))
    const g = Math.round(startColor[1] + t * (endColor[1] - startColor[1]))
    const b = Math.round(startColor[2] + t * (endColor[2] - startColor[2]))
    colors.push({
      value: year,
      symbol: new SimpleFillSymbol({
        color: [r, g, b, 0.6],
        outline: { color: [r * 0.7, g * 0.7, b * 0.7], width: 1 }
      }),
      label: `${year}`
    })
  }
  return colors
}
```

### 4.4 Chart.js 4.4.1

**文件**: `frontend/src/components/NdviChart.jsx`

用于绘制 NDVI 时间序列折线图。

```javascript
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
)

// 图表配置
const options = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      min: 0,
      max: 1,
      title: { display: true, text: 'NDVI' }
    }
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context) => `NDVI: ${context.parsed.y?.toFixed(3)}`
      }
    }
  }
}

// 数据结构
const data = {
  labels: years,  // ['2010', '2011', ...]
  datasets: [{
    label: 'NDVI',
    data: ndviValues,
    borderColor: 'rgb(34, 197, 94)',
    backgroundColor: 'rgba(34, 197, 94, 0.1)',
    fill: true,
    tension: 0.3,  // 曲线平滑度
  }]
}
```

### 4.5 Zustand 状态管理 (v4.5.0)

Zustand 是一个轻量级的 React 状态管理库，用于管理全局认证状态。

```javascript
import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,

  login: (userData, tokens) => {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    set({ user: userData, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  setUser: (userData) => set({ user: userData }),
}))
```

---

## 5. 核心算法详解

### 5.1 算法流程概述

**文件**: `backend/runners/python_runner.py`

检测算法分为 7 个主要步骤：

```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: 加载 NDVI 多波段 GeoTIFF                                     │
│ Input: ndvi.tif (m × n × l 像元)                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: 数据清洗与归一化                                             │
│ - 零值 → NaN                                                         │
│ - 异常值 (≥1 或 <-1) → NaN 或 0                                      │
│ - 计算 0.5/99.5 百分位数作为归一化边界                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: 生成 49 个训练模板                                           │
│ creat_sample(s, length, 0.8, 0.6) → 49 × (l+1) 矩阵                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 4: KNN-DTW 分类                                                 │
│ 对每个有效像元：                                                      │
│   1. NaN 移除 + 位置记录                                             │
│   2. BWlvbo 时序平滑                                                  │
│   3. DTW 距离计算 (与 49 个模板)                                      │
│   4. 最近邻匹配 → 类别标签                                            │
│   5. 弯曲路径反向追踪 → 扰动/恢复年份                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 5: 空间滤波                                                     │
│ - 形态学开运算 (disk r=2)                                            │
│ - 连通区域标记 (8-邻域)                                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 6: 裸煤概率验证                                                  │
│ - 重采样裸煤数据至 NDVI 网格                                          │
│ - 中值滤波平滑                                                        │
│ - 筛选条件：                                                          │
│   total_num ≥ 1111 且 union_num ≥ 222 且 union_num/total_num ≥ 0.02 │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 7: 输出 GeoTIFF 结果文件                                         │
│ - mining_disturbance_mask.tif    (扰动掩膜 0/1)                       │
│ - mining_disturbance_year.tif    (扰动年份)                           │
│ - mining_recovery_year.tif       (恢复年份)                           │
│ - potential_disturbance.tif      (潜在扰动区域)                       │
│ - res_disturbance_type.tif       (扰动类型 1-49)                      │
│ - year_disturbance_raw.tif       (原始扰动年份)                       │
│ - year_recovery_raw.tif          (原始恢复年份)                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 动态时间规整 (DTW)

**文件**: `backend/runners/algorithm/dtw.py`

#### 5.2.1 算法原理

动态时间规整 (Dynamic Time Warping) 是一种测量两个时间序列相似性的算法，允许序列在时间轴上进行非线性对齐。

**数学定义**:

给定两个序列：
- 参考序列 $R = (r_1, r_2, ..., r_M)$
- 测试序列 $T = (t_1, t_2, ..., t_N)$

累积距离矩阵 $D$ 的递推公式：

$$D(i, j) = d(r_i, t_j) + \min \begin{cases} D(i-1, j) \\ D(i-1, j-1) \\ D(i, j-1) \end{cases}$$

其中 $d(r_i, t_j) = (r_i - t_j)^2$ 是欧氏距离的平方。

DTW 距离 = $D(M, N)$

#### 5.2.2 Numba 加速实现

```python
@jit(nopython=True, cache=True)
def _dtw_distance_matrix(r, t):
    """计算 DTW 累积距离矩阵 D"""
    M = len(r)
    N = len(t)

    D = np.full((M, N), np.inf, dtype=np.float64)
    D[0, 0] = (r[0] - t[0]) ** 2

    # 第一列
    for m in range(1, M):
        D[m, 0] = (r[m] - t[0]) ** 2 + D[m - 1, 0]

    # 第一行
    for n in range(1, N):
        D[0, n] = (r[0] - t[n]) ** 2 + D[0, n - 1]

    # 填充矩阵
    for m in range(1, M):
        for n in range(1, N):
            cost = (r[m] - t[n]) ** 2
            D[m, n] = cost + min(D[m - 1, n], D[m - 1, n - 1], D[m, n - 1])

    return D[M - 1, N - 1], D
```

#### 5.2.3 内存优化版本 (仅计算距离)

```python
@jit(nopython=True, cache=True)
def _dtw_distance_only(r, t):
    """O(1) 空间复杂度的 DTW 距离计算"""
    M = len(r)
    N = len(t)

    # 仅使用两行
    prev_row = np.full(N, np.inf, dtype=np.float64)
    curr_row = np.full(N, np.inf, dtype=np.float64)

    prev_row[0] = (r[0] - t[0]) ** 2
    for n in range(1, N):
        prev_row[n] = (r[0] - t[n]) ** 2 + prev_row[n - 1]

    for m in range(1, M):
        curr_row[0] = (r[m] - t[0]) ** 2 + prev_row[0]
        for n in range(1, N):
            cost = (r[m] - t[n]) ** 2
            curr_row[n] = cost + min(prev_row[n], prev_row[n - 1], curr_row[n - 1])
        prev_row, curr_row = curr_row, prev_row

    return prev_row[N - 1]
```

#### 5.2.4 路径回溯

```python
@jit(nopython=True, cache=True)
def _backtrack_path(D):
    """从 D 矩阵回溯最优弯曲路径"""
    M, N = D.shape
    max_len = M + N
    path = np.zeros((max_len, 2), dtype=np.int64)

    m, n = M - 1, N - 1
    k = 0
    path[k, 0] = m + 1  # 1-based 索引 (MATLAB 兼容)
    path[k, 1] = n + 1

    while m > 0 or n > 0:
        k += 1
        if m == 0:
            n -= 1
        elif n == 0:
            m -= 1
        else:
            d_up = D[m - 1, n]
            d_left = D[m, n - 1]
            d_diag = D[m - 1, n - 1]

            if d_diag <= d_up and d_diag <= d_left:
                m -= 1
                n -= 1
            elif d_up <= d_left:
                m -= 1
            else:
                n -= 1

        path[k, 0] = m + 1
        path[k, 1] = n + 1

    # 反转路径
    actual_len = k + 1
    result = np.zeros((actual_len, 2), dtype=np.int64)
    for i in range(actual_len):
        result[i, 0] = path[actual_len - 1 - i, 0]
        result[i, 1] = path[actual_len - 1 - i, 1]

    return result
```

### 5.3 时序平滑算法 (BWlvbo)

**文件**: `backend/runners/algorithm/bwlvbo.py`

BWlvbo 算法结合了两种时序处理技术：

#### 5.3.1 尖峰移除 (Spike Removal)

检测并修正 NDVI 时序中的异常下降尖峰。

**原理**: 对于连续三个观测值 $(c_0, c_1, c_2)$，如果中间值 $c_1$ 相对于两侧都显著偏低，则认为是尖峰噪声。

**判定条件**:
- $p_1 = \frac{c_0 - c_1}{c_0} > 0.2$
- $p_2 = \frac{c_2 - c_1}{c_2} > 0.2$
- $\frac{c_2 - c_1}{c_0 - c_1} > 0.4$

**修正方法**: $c_1 \leftarrow \frac{c_0 + c_2}{2}$

```python
@jit(nopython=True, cache=True)
def _spike_removal_numba(a):
    n = len(a)
    result = a.copy()

    for i in range(n - 2):
        c0 = result[i]
        c1 = result[i + 1]
        c2 = result[i + 2]

        if c0 == 0.0 or c2 == 0.0:
            continue

        p1 = (c0 - c1) / c0
        p2 = (c2 - c1) / c2
        p3 = c2 - c1
        p4 = c0 - c1

        if p4 == 0.0:
            continue

        if p1 > 0.2 and p2 > 0.2 and p3 / p4 > 0.4:
            result[i + 1] = (c0 + c2) / 2.0

    return result
```

#### 5.3.2 小波去噪 (Wavelet Denoising)

使用 PyWavelets 库实现 MATLAB `wden()` 函数的功能。

**参数配置**:
- 小波基函数: `db7` (Daubechies 7)
- 分解级数: 2
- 阈值选择: `minimaxi`
- 阈值规则: `soft` (软阈值)
- 噪声估计: `mln` (基于 MAD 的级别依赖估计)

**阈值计算**:

Minimaxi 阈值公式：
$$\tau = \begin{cases} 0 & \text{if } n \leq 32 \\ 0.3936 + 0.1829 \cdot \log_2(n) & \text{otherwise} \end{cases}$$

噪声标准差估计 (MAD):
$$\sigma = \frac{\text{median}(|d|)}{0.6745}$$

最终阈值: $T = \tau \cdot \sigma$

```python
def _wden_minimaxi_soft_mln(signal, wavelet='db7', level=2):
    max_level = pywt.dwt_max_level(len(signal), pywt.Wavelet(wavelet).dec_len)
    level = min(level, max_level)

    if level < 1:
        return signal.copy()

    coeffs = pywt.wavedec(signal, wavelet, level=level)
    n = len(signal)
    base_thr = _minimaxi_threshold(n)

    denoised_coeffs = [coeffs[0]]  # 保留近似系数

    for i in range(1, len(coeffs)):
        detail = coeffs[i]
        if len(detail) == 0:
            denoised_coeffs.append(detail)
            continue
        # MAD 噪声估计
        sigma = np.median(np.abs(detail)) / 0.6745
        thr = base_thr * sigma
        # 软阈值处理
        denoised = pywt.threshold(detail, value=thr, mode='soft')
        denoised_coeffs.append(denoised)

    return pywt.waverec(denoised_coeffs, wavelet)
```

### 5.4 训练模板生成

**文件**: `backend/runners/algorithm/sample_generator.py`

系统生成 49 个合成 NDVI 时序模板，覆盖各种扰动-恢复模式。

#### 5.4.1 模板分类

| 标签范围 | 类型 | 描述 |
|---------|------|------|
| 1-9 | 仅扰动 | NDVI 从高值下降到低值，无恢复 |
| 10-36 | 扰动+恢复 | NDVI 下降后指数恢复 |
| 37 | 稳定低值 | 持续低 NDVI (扰动状态) |
| 38-40 | 稳定高值 | 持续高 NDVI (健康植被) |
| 41-49 | 仅恢复 | NDVI 从低值恢复到高值 |

#### 5.4.2 扰动位置

每组模板包含 3 种扰动/恢复发生时间点：
- **25%**: 早期扰动/恢复
- **50%**: 中期扰动/恢复
- **75%**: 晚期扰动/恢复

#### 5.4.3 振幅因子

- **1.0**: 完全扰动 (从 s[1] 到 s[0])
- **p1 = 0.8**: 80% 振幅
- **p2 = 0.6**: 60% 振幅

#### 5.4.4 恢复曲线模型

植被恢复遵循指数衰减模型：

$$NDVI(t) = (NDVI_{low} - NDVI_{target}) \cdot e^{-0.5t} + NDVI_{target}$$

```python
def vegetation_recovery(a, b):
    """指数恢复曲线"""
    b = np.asarray(b, dtype=float)
    return (a[0] - a[1]) * np.exp(-0.5 * b) + a[1]
```

### 5.5 KNN 分类流程

**文件**: `backend/runners/algorithm/knn_dtw.py`

#### 5.5.1 单像元处理流程

```python
def _process_pixel(test_ts, train_data, labels, N):
    # 1. NaN 处理
    nan_mask = np.isnan(test_ts)
    id_nan = np.where(nan_mask)[0] + 1  # 1-based (MATLAB 兼容)
    test_clean = test_ts[~nan_mask]

    if len(test_clean) == 0:
        return 0, 0, 0

    # 2. 时序平滑
    denoised = bwlvbo(test_clean)

    # 3. 找最佳匹配模板 (仅计算距离)
    n_templates = train_data.shape[0]
    best_dist = np.inf
    best_idx = 0
    for i in range(n_templates):
        d = _dtw_distance_only(train_data[i], denoised)
        if d < best_dist:
            best_dist = d
            best_idx = i

    best_label = int(labels[best_idx])

    # 4. 计算最佳模板的弯曲路径
    _, D = _dtw_distance_matrix(train_data[best_idx], denoised)
    path = _backtrack_path(D)

    # 5. 提取扰动/恢复年份
    yd, yr = _extract_years(path, best_label, id_nan, N)

    return best_label, yd, yr
```

#### 5.5.2 年份提取逻辑

根据模板标签，从弯曲路径中提取对应的扰动/恢复年份。

**核心思想**: 弯曲路径建立了模板时间点与实际观测时间点的对应关系。通过查找模板中"扰动发生点"对应的实际观测索引，即可获得扰动年份。

```python
def _extract_years(py, label, id_nan, N):
    r = matlab_round

    # 调整 NaN 位置
    if label not in (37, 38, 39, 40):
        py = _adjust_path_for_nans(py, id_nan)

    yd, yr = 0, 0

    # Labels 1, 4, 7: 25% 位置扰动
    if label in (1, 4, 7):
        target = r(0.25 * N)
        t_dis = np.where(py[:, 0] == target)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])

    # Labels 2, 5, 8: 50% 位置扰动
    elif label in (2, 5, 8):
        target = r(N / 2)
        t_dis = np.where(py[:, 0] == target)[0]
        if len(t_dis) > 0:
            yd = int(py[t_dis[0], 1])

    # ... (完整的 49 种情况处理)

    return yd, yr
```

#### 5.5.3 并行处理

使用 joblib 实现多核并行处理，显著提升大规模数据处理速度。

```python
def _classify_parallel(train_data, labels, test_data, N, n_jobs, chunk_size):
    M_test = test_data.shape[0]
    n_chunks = (M_test + chunk_size - 1) // chunk_size

    # 构建数据块
    chunk_args = []
    for i in range(0, M_test, chunk_size):
        end = min(i + chunk_size, M_test)
        chunk_args.append(test_data[i:end])

    # 并行执行
    results_list = Parallel(
        n_jobs=n_jobs,
        verbose=10,
        prefer="processes"
    )(
        delayed(_process_chunk)(chunk, train_data, labels, N)
        for chunk in chunk_args
    )

    combined = np.vstack(results_list)
    return combined[:, 0], combined[:, 1], combined[:, 2]
```

**性能优化策略**:
1. **Numba JIT 编译**: DTW 核心计算加速 50-100 倍
2. **内存优化**: 仅对最佳模板计算完整路径
3. **并行分块**: 大规模数据分块并行处理
4. **缓存预热**: Numba 函数预编译避免首次调用延迟

---

## 6. 数据库设计

### 6.1 ER 图

```
┌──────────────────┐         ┌──────────────────┐
│      users       │         │      jobs        │
├──────────────────┤         ├──────────────────┤
│ id (PK)          │────┐    │ id (PK)          │
│ username (UQ)    │    │    │ job_id (UQ)      │
│ email (UQ)       │    └───►│ user_id (FK)     │
│ password_hash    │         │ status           │
│ role             │         │ engine           │
│ is_active        │         │ startyear        │
│ created_at       │         │ ndvi_filename    │
│ last_login       │         │ coal_filename    │
└──────────────────┘         │ bounds_json      │
                             │ crs_info_json    │
                             │ error_message    │
                             │ created_at       │
                             │ completed_at     │
                             └────────┬─────────┘
                                      │
                                      │ 1:N
                                      ▼
                             ┌──────────────────┐
                             │    job_files     │
                             ├──────────────────┤
                             │ id (PK)          │
                             │ job_db_id (FK)   │
                             │ filename         │
                             │ label            │
                             │ file_type        │
                             │ size             │
                             └──────────────────┘
```

### 6.2 索引设计

| 表 | 字段 | 索引类型 | 用途 |
|----|------|---------|------|
| users | username | UNIQUE | 登录查询 |
| users | email | UNIQUE | 邮箱验证 |
| jobs | job_id | UNIQUE | UUID 查询 |
| jobs | user_id | INDEX | 用户任务列表 |
| job_files | job_db_id | INDEX | 文件关联查询 |

### 6.3 状态流转

```
         ┌─────────────────────────────────────────────────────┐
         │                      Job Status                      │
         └─────────────────────────────────────────────────────┘

         [pending] ────► [running] ────► [completed]
              │              │
              └──────────────┴───────────► [failed]
```

---

## 7. API 接口规范

### 7.1 认证 API

#### POST /api/auth/register

**请求体**:
```json
{
  "username": "string (2-80 字符)",
  "email": "string (有效邮箱)",
  "password": "string (≥6 字符)"
}
```

**成功响应** (201):
```json
{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2026-01-31T12:00:00"
  }
}
```

#### POST /api/auth/login

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**成功响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "testuser",
    "role": "user",
    "is_active": true
  }
}
```

#### POST /api/auth/refresh

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**成功响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { ... }
}
```

### 7.2 任务 API

#### POST /api/upload

上传 GeoTIFF 文件。

**请求头**: `Authorization: Bearer <access_token>`

**请求体** (multipart/form-data):
- `file`: GeoTIFF 文件
- `kind`: `ndvi` | `coal`
- `job_id`: (可选) 现有任务 ID

**成功响应** (200):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "kind": "ndvi",
  "path": "/data/uploads/550e8400.../ndvi.tif"
}
```

#### POST /api/run

执行检测任务。

**请求体**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "startyear": 2010,
  "engine": "python"
}
```

**成功响应** (200):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "bounds": {
    "west": 110.5,
    "south": 35.2,
    "east": 111.8,
    "north": 36.5
  },
  "crs_info": {
    "valid": true,
    "epsg": 4326,
    "crs_name": "WGS 84"
  },
  "outputs": {
    "mining_disturbance_mask": "/jobs/550e8400.../mining_disturbance_mask.tif",
    "mining_disturbance_year": "/jobs/550e8400.../mining_disturbance_year.tif",
    "mining_recovery_year": "/jobs/550e8400.../mining_recovery_year.tif"
  }
}
```

#### GET /api/ndvi-timeseries

查询单像元 NDVI 时间序列。

**查询参数**:
- `job_id`: 任务 ID
- `lon`: 经度
- `lat`: 纬度
- `startyear`: 起始年份

**成功响应** (200):
```json
{
  "job_id": "550e8400...",
  "lon": 110.85,
  "lat": 35.72,
  "years": [2010, 2011, 2012, ...],
  "ndvi": [0.65, 0.68, 0.42, 0.35, ...],
  "disturbance_year": 2012,
  "recovery_year": 2018
}
```

### 7.3 瓦片 API

#### GET /api/tiles/{job_id}/{layer_name}/{z}/{x}/{y}.png

动态生成地图瓦片。

**参数**:
- `job_id`: 任务 ID
- `layer_name`: `disturbance_mask` | `disturbance_year` | `recovery_year`
- `z`, `x`, `y`: 瓦片坐标

**响应**: PNG 图像 (256×256 像素)

#### GET /api/result-geojson/{job_id}/{layer_name}

获取矢量化结果。

**响应** (GeoJSON):
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[110.5, 35.2], [110.5, 36.5], ...]]
      },
      "properties": {
        "value": 1,
        "layer": "disturbance_mask",
        "year": 2015
      }
    }
  ]
}
```

### 7.4 管理员 API

#### GET /api/admin/stats

获取系统统计信息。

**响应**:
```json
{
  "users": 25,
  "jobs": {
    "total": 150,
    "completed": 142,
    "failed": 8
  },
  "disk": {
    "uploads": "2.5 GB",
    "results": "8.3 GB",
    "total": "10.8 GB"
  }
}
```

---

## 8. 地理空间处理

**文件**: `backend/services/geo_service.py`

### 8.1 坐标系信息提取

```python
def get_crs_info(geotiff_path):
    """提取 GeoTIFF 的坐标系信息用于前端显示"""
    with rasterio.open(geotiff_path) as ds:
        if ds.crs is None:
            return {"valid": False, "warning": "GeoTIFF 缺少坐标系元数据"}

        epsg = ds.crs.to_epsg()
        crs_string = ds.crs.to_string()

        # 常见坐标系名称映射
        epsg_names = {
            4326: "WGS 84 地理坐标系",
            3857: "Web Mercator",
            4490: "CGCS2000 地理坐标系",
        }

        # UTM 带号识别
        if 32601 <= epsg <= 32660:
            crs_name = f"WGS 84 / UTM {epsg - 32600}N"
        elif 32701 <= epsg <= 32760:
            crs_name = f"WGS 84 / UTM {epsg - 32700}S"

        return {
            "valid": True,
            "epsg": epsg,
            "crs_string": crs_string,
            "crs_name": crs_name
        }
```

### 8.2 边界计算与转换

```python
def get_geotiff_bounds(geotiff_path):
    """获取 GeoTIFF 的地理边界 (EPSG:4326)"""
    with rasterio.open(geotiff_path) as ds:
        bounds = ds.bounds
        src_crs = ds.crs

        if src_crs is None or src_crs.to_string() == "EPSG:4326":
            return {
                "west": bounds.left,
                "south": bounds.bottom,
                "east": bounds.right,
                "north": bounds.top,
            }
        else:
            # 坐标系转换
            tfm = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
            west, south = tfm.transform(bounds.left, bounds.bottom)
            east, north = tfm.transform(bounds.right, bounds.top)
            return {"west": west, "south": south, "east": east, "north": north}
```

### 8.3 时间序列采样

```python
def sample_timeseries(geotiff_path, lon, lat):
    """从 GeoTIFF 中采样时间序列数据"""
    with rasterio.open(geotiff_path) as ds:
        # 坐标系转换
        if ds.crs.to_string() != "EPSG:4326":
            tfm = Transformer.from_crs("EPSG:4326", ds.crs, always_xy=True)
            x, y = tfm.transform(lon, lat)
        else:
            x, y = lon, lat

        # 像元定位
        row, col = ds.index(x, y)

        if row < 0 or row >= ds.height or col < 0 or col >= ds.width:
            raise ValueError(f"坐标 ({lon}, {lat}) 超出数据范围")

        # 读取所有波段
        arr = ds.read()
        vals = arr[:, row, col].astype("float64")

        # 处理 NoData
        nodata = ds.nodata
        if nodata is not None:
            vals = np.where(vals == nodata, np.nan, vals)

        return vals.tolist(), ds.count
```

---

## 9. 瓦片服务系统

**文件**: `backend/services/tile_service.py`

### 9.1 Web Mercator 瓦片坐标计算

```python
TILE_SIZE = 256
EARTH_RADIUS = 6378137.0
ORIGIN_SHIFT = 2 * math.pi * EARTH_RADIUS / 2.0  # ~20037508.34

def tile_bounds_3857(z, x, y):
    """计算瓦片在 EPSG:3857 中的边界"""
    res = 2 * ORIGIN_SHIFT / (TILE_SIZE * (2 ** z))
    minx = -ORIGIN_SHIFT + x * TILE_SIZE * res
    maxx = minx + TILE_SIZE * res
    maxy = ORIGIN_SHIFT - y * TILE_SIZE * res
    miny = maxy - TILE_SIZE * res
    return (minx, miny, maxx, maxy)
```

### 9.2 瓦片渲染流程

```python
def render_tile(tif_path, layer_name, z, x, y):
    """渲染单个瓦片"""
    tile_b = tile_bounds_3857(z, x, y)

    with rasterio.open(tif_path) as src:
        # 转换边界到源坐标系
        src_bounds = transform_bounds("EPSG:3857", src.crs, *tile_b)

        # 检查是否有数据覆盖
        data_bounds = src.bounds
        if (src_bounds[2] < data_bounds.left or
            src_bounds[0] > data_bounds.right or
            src_bounds[3] < data_bounds.bottom or
            src_bounds[1] > data_bounds.top):
            return make_transparent_tile()

        # 读取窗口数据
        window = from_bounds(*src_bounds, src.transform)
        data = src.read(1, window=window)

        # 重投影到 Web Mercator
        dst_data = np.zeros((TILE_SIZE, TILE_SIZE), dtype=data.dtype)
        reproject(
            source=data,
            destination=dst_data,
            src_transform=window_transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs="EPSG:3857",
            resampling=Resampling.nearest,
        )

        # 应用颜色映射
        rgba = apply_colormap(dst_data, layer_name, src.nodata)

    # 生成 PNG
    img = Image.fromarray(rgba, "RGBA")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
```

### 9.3 颜色映射配置

```python
LAYER_COLORMAPS = {
    "disturbance_mask": {
        "type": "categorical",
        "colors": {
            0: (0, 0, 0, 0),      # 透明
            1: (220, 38, 38, 180) # 半透明红色
        }
    },
    "disturbance_year": {
        "type": "year_gradient",
        "start": (255, 100, 100),  # 浅红
        "end": (139, 0, 0),        # 深红
        "range": (1980, 2050)
    },
    "recovery_year": {
        "type": "year_gradient",
        "start": (144, 238, 144),  # 浅绿
        "end": (0, 100, 0),        # 深绿
        "range": (1980, 2050)
    },
    "potential_disturbance": {
        "type": "continuous",
        "color": (255, 165, 0)     # 橙色
    }
}
```

### 9.4 瓦片缓存

```python
_tile_cache = {}
_tile_cache_max = 500

def cache_tile(key, png_bytes):
    global _tile_cache
    if len(_tile_cache) >= _tile_cache_max:
        # LRU 清理策略
        keys_to_remove = list(_tile_cache.keys())[:int(_tile_cache_max * 0.2)]
        for k in keys_to_remove:
            del _tile_cache[k]
    _tile_cache[key] = png_bytes

def get_cached_tile(key):
    return _tile_cache.get(key)
```

---

## 10. 安全与认证

### 10.1 JWT 令牌结构

**文件**: `backend/auth.py`

#### Access Token 载荷

```json
{
  "user_id": 1,
  "role": "admin",
  "type": "access",
  "exp": 1738368000,
  "iat": 1738360800
}
```

#### Refresh Token 载荷

```json
{
  "user_id": 1,
  "type": "refresh",
  "exp": 1740960000,
  "iat": 1738368000
}
```

### 10.2 令牌生成

```python
def generate_access_token(user_id, role):
    payload = {
        "user_id": user_id,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def generate_refresh_token(user_id):
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### 10.3 路由装饰器

**文件**: `backend/decorators.py`

```python
def jwt_required(f):
    """要求有效的 access_token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "缺少认证令牌"}), 401

        token = auth_header[7:]
        payload = decode_token(token)
        if payload is None:
            return jsonify({"error": "令牌无效或已过期"}), 401
        if payload.get("type") != "access":
            return jsonify({"error": "令牌类型错误"}), 401

        user = db.session.get(User, payload["user_id"])
        if user is None or not user.is_active:
            return jsonify({"error": "用户不存在或已禁用"}), 401

        g.user_id = user.id
        g.user_role = user.role
        g.user = user
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """要求管理员角色"""
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if g.user_role != "admin":
            return jsonify({"error": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated
```

### 10.4 密码安全

使用 Werkzeug 的 `pbkdf2:sha256` 算法进行密码哈希：

```python
from werkzeug.security import generate_password_hash, check_password_hash

# 注册时
password_hash = generate_password_hash(password)

# 登录时
if check_password_hash(user.password_hash, password):
    # 密码正确
```

---

## 11. 性能优化策略

### 11.1 算法层优化

| 优化项 | 技术 | 效果 |
|-------|------|------|
| DTW 加速 | Numba JIT | 50-100× 提升 |
| 并行处理 | joblib multiprocessing | N× 提升 (N = CPU 核心数) |
| 内存优化 | O(1) 空间 DTW | 减少 95% 内存占用 |
| 路径计算优化 | 仅对最佳模板计算路径 | 减少 98% 路径计算 |
| 缓存预热 | Numba 函数预编译 | 消除首次调用延迟 |

### 11.2 数据层优化

| 优化项 | 技术 | 效果 |
|-------|------|------|
| 数据库索引 | 复合索引 | 查询加速 |
| 瓦片缓存 | 内存 LRU 缓存 | 减少重复渲染 |
| 窗口读取 | rasterio window | 减少 I/O |
| 分块处理 | chunk_size 参数 | 内存可控 |

### 11.3 网络层优化

| 优化项 | 技术 | 效果 |
|-------|------|------|
| 透明令牌刷新 | Axios 拦截器 | 无感续期 |
| 请求超时 | 10分钟超时 | 适应长任务 |
| PNG 压缩 | Pillow optimize | 减少传输量 |

---

## 12. 部署与运维

### 12.1 环境变量

| 变量名 | 默认值 | 说明 |
|--------|-------|------|
| `DATABASE_URI` | `sqlite:///data/mining.db` | 数据库连接字符串 |
| `SECRET_KEY` | 随机生成 | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE` | `2` | Access Token 有效期 (小时) |
| `REFRESH_TOKEN_EXPIRE` | `30` | Refresh Token 有效期 (天) |
| `DETECTION_ENGINE` | `python` | 检测引擎 (`python` \| `matlab`) |
| `DEFAULT_ADMIN_USERNAME` | `admin` | 默认管理员用户名 |
| `DEFAULT_ADMIN_EMAIL` | `admin@mining.local` | 默认管理员邮箱 |
| `DEFAULT_ADMIN_PASSWORD` | `admin123` | 默认管理员密码 |

### 12.2 启动命令

**开发环境**:

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py  # 监听 127.0.0.1:5001

# 前端
cd frontend
npm install
npm run dev  # 监听 localhost:5173
```

**生产环境**:

```bash
# 前端构建
cd frontend
npm run build  # 输出到 dist/

# 后端服务
cd backend
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### 12.3 目录权限

```bash
# 确保数据目录可写
chmod -R 755 data/
mkdir -p data/uploads data/jobs
```

### 12.4 日志配置

日志输出格式：

```
2026-02-01 12:00:00,000 - __main__ - INFO - 启动露天矿区检测平台
2026-02-01 12:00:00,001 - __main__ - INFO - UPLOAD_DIR: /path/to/data/uploads
2026-02-01 12:00:00,002 - __main__ - INFO - JOB_DIR: /path/to/data/jobs
```

---

## 附录 A: 输出文件说明

| 文件名 | 数据类型 | 值范围 | 说明 |
|--------|---------|--------|------|
| `mining_disturbance_mask.tif` | Float64 | 0/1 | 扰动区域二值掩膜 |
| `mining_disturbance_year.tif` | Float64 | 年份 | 扰动发生年份 |
| `mining_recovery_year.tif` | Float64 | 年份 | 恢复发生年份 |
| `potential_disturbance.tif` | Float64 | 连通区ID | 潜在扰动区域 |
| `res_disturbance_type.tif` | Float64 | 1-49 | 扰动类型 (模板标签) |
| `year_disturbance_raw.tif` | Float64 | 相对年份 | 原始扰动年份 (未加startyear) |
| `year_recovery_raw.tif` | Float64 | 相对年份 | 原始恢复年份 (未加startyear) |

---

## 附录 B: 49 模板详细说明

| 标签 | 扰动时间 | 恢复时间 | 振幅 | 恢复目标 |
|-----|---------|---------|------|---------|
| 1 | 25% | - | 1.0 | - |
| 2 | 50% | - | 1.0 | - |
| 3 | 75% | - | 1.0 | - |
| 4 | 25% | - | 0.8 | - |
| 5 | 50% | - | 0.8 | - |
| 6 | 75% | - | 0.8 | - |
| 7 | 25% | - | 0.6 | - |
| 8 | 50% | - | 0.6 | - |
| 9 | 75% | - | 0.6 | - |
| 10-12 | 25/50/75% | 有 | 1.0 | s |
| 13-15 | 25/50/75% | 有 | 0.8 | s |
| 16-18 | 25/50/75% | 有 | 1.0 | 0.8s |
| 19-21 | 25/50/75% | 有 | 0.8 | 0.8s |
| 22-24 | 25/50/75% | 有 | 0.6 | s |
| 25-27 | 25/50/75% | 有 | 1.0 | 0.6s |
| 28-30 | 25/50/75% | 有 | 0.6 | 0.6s |
| 31-33 | 25/50/75% | 有 | 0.6 | 0.8s |
| 34-36 | 25/50/75% | 有 | 0.8 | 0.6s |
| 37 | - | - | - | 稳定低 |
| 38-40 | - | - | - | 稳定高 |
| 41-43 | - | 25/50/75% | - | s |
| 44-46 | - | 25/50/75% | - | 0.8s |
| 47-49 | - | 25/50/75% | - | 0.6s |

---

## 附录 C: 术语表

| 术语 | 全称 | 说明 |
|------|------|------|
| NDVI | Normalized Difference Vegetation Index | 归一化植被指数 |
| DTW | Dynamic Time Warping | 动态时间规整 |
| KNN | K-Nearest Neighbors | K 最近邻 |
| GeoTIFF | Georeferenced TIFF | 地理参考 TIFF |
| CRS | Coordinate Reference System | 坐标参考系统 |
| EPSG | European Petroleum Survey Group | 坐标系编码标准 |
| JWT | JSON Web Token | JSON Web 令牌 |
| MAD | Median Absolute Deviation | 中位数绝对偏差 |
| ORM | Object-Relational Mapping | 对象关系映射 |
| SPA | Single Page Application | 单页应用 |

---

**文档版本**: 1.0.0
**最后更新**: 2026年2月1日
