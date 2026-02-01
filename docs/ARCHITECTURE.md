# 矿区检测平台 - 系统架构文档

## 1. 系统概述

矿区检测平台是一个基于 KNN-DTW 算法的矿区扰动检测系统，通过分析 NDVI 时间序列数据和裸煤概率图，识别潜在的矿区扰动区域。

### 1.1 核心功能
- 用户认证与权限管理
- GeoTIFF 文件上传与处理
- 矿区扰动检测算法运行
- 检测结果可视化（地图 + 图表）
- 历史任务管理
- 结果文件下载
- 管理员后台

### 1.2 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + Zustand |
| 地图 | ArcGIS Maps SDK for JavaScript 4.29 |
| 图表 | Chart.js 4.x |
| 后端 | Flask 3.x + SQLAlchemy |
| 认证 | JWT (PyJWT) |
| 数据库 | SQLite |
| 算法 | Python (NumPy, Rasterio, Scikit-learn) |

---

## 2. 目录结构

```
mining_platform/
├── backend/                      # Flask 后端
│   ├── app.py                    # 主入口 (create_app)
│   ├── config.py                 # 配置文件
│   ├── models.py                 # SQLAlchemy 模型
│   ├── auth.py                   # JWT 认证模块
│   ├── decorators.py             # 路由装饰器
│   ├── init_db.py                # 数据库初始化
│   ├── requirements.txt          # Python 依赖
│   ├── routes/                   # 路由蓝图
│   │   ├── auth_routes.py        # 认证 API
│   │   ├── user_routes.py        # 用户 API
│   │   ├── job_routes.py         # 检测任务 API
│   │   ├── tile_routes.py        # 瓦片服务 API
│   │   └── admin_routes.py       # 管理员 API
│   ├── services/                 # 业务逻辑层
│   │   ├── geo_service.py        # 地理处理服务
│   │   └── tile_service.py       # 瓦片渲染服务
│   └── runners/                  # 算法运行器
│       ├── base_runner.py        # 运行器基类
│       ├── python_runner.py      # Python 运行器
│       └── algorithm/            # 核心算法
│           └── knndtw_detector.py
├── frontend/                     # React 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── dist/                     # 构建产物
│   └── src/
│       ├── main.jsx
│       ├── App.jsx               # 路由配置
│       ├── api/client.js         # Axios 客户端
│       ├── store/authStore.js    # Zustand 状态
│       ├── components/           # 通用组件
│       ├── pages/                # 页面组件
│       └── styles/index.css      # 全局样式
├── frontend_legacy/              # 旧版前端备份
├── data/
│   ├── mining.db                 # SQLite 数据库
│   ├── uploads/                  # 上传文件
│   └── jobs/                     # 任务输出
└── docs/                         # 技术文档
```

---

## 3. 后端架构

### 3.1 应用工厂模式

`app.py` 使用 Flask 应用工厂模式：

```python
def create_app():
    app = Flask(__name__, static_folder='../frontend/dist')

    # 加载配置
    app.config.from_object(Config)

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(tile_bp)
    app.register_blueprint(admin_bp)

    return app
```

### 3.2 蓝图模块化

| 蓝图 | 前缀 | 功能 |
|------|------|------|
| auth_bp | /api/auth | 注册、登录、刷新Token |
| user_bp | /api/user | 个人信息、修改密码 |
| job_bp | /api | 上传、运行、历史记录 |
| tile_bp | /api | 瓦片、GeoJSON |
| admin_bp | /api/admin | 管理员功能 |

### 3.3 认证流程

```
客户端                                     服务端
   |                                          |
   |-------- POST /api/auth/login ----------->|
   |         {username, password}             |
   |                                          |
   |<------- {access_token, refresh_token} ---|
   |                                          |
   |-------- GET /api/jobs ------------------>|
   |         Authorization: Bearer <token>    |
   |                                          |
   |<------- {jobs: [...]} -------------------|
   |                                          |
   |  (access_token 过期后)                    |
   |                                          |
   |-------- POST /api/auth/refresh --------->|
   |         {refresh_token}                  |
   |                                          |
   |<------- {access_token} ------------------|
```

### 3.4 服务层

- **geo_service.py**: 地理空间处理
  - `get_crs_info()`: 获取坐标系信息
  - `get_geotiff_bounds()`: 获取栅格边界
  - `sample_timeseries()`: 采样时间序列
  - `sample_singleband()`: 采样单波段值

- **tile_service.py**: 瓦片渲染
  - `get_or_render_tile()`: 获取或渲染瓦片
  - `apply_colormap()`: 应用颜色映射
  - 内置瓦片缓存机制

---

## 4. 前端架构

### 4.1 路由配置

```jsx
<Routes>
  <Route path="/" element={<LandingPage />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />

  <Route element={<Layout />}>
    <Route element={<ProtectedRoute />}>
      <Route path="/detect" element={<DetectionPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/profile" element={<ProfilePage />} />
    </Route>

    <Route element={<ProtectedRoute requireAdmin />}>
      <Route path="/admin" element={<Dashboard />} />
      <Route path="/admin/users" element={<UserManage />} />
      <Route path="/admin/jobs" element={<JobManage />} />
    </Route>
  </Route>
</Routes>
```

### 4.2 状态管理

使用 Zustand 管理认证状态：

```javascript
const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      login: async (username, password) => { ... },
      logout: () => { ... },
      isAdmin: () => get().user?.role === 'admin',
    }),
    { name: 'auth-storage' }
  )
)
```

### 4.3 API 客户端

Axios 实例配置：
- 请求拦截器：自动附加 Authorization 头
- 响应拦截器：401 时自动刷新 Token

### 4.4 ArcGIS 集成

由于 ArcGIS 使用 AMD 模块系统，采用以下方式集成：

1. 在 `index.html` 通过 CDN 加载 ArcGIS SDK
2. React 组件中使用 `window.require` 加载模块
3. 使用 `useRef` + `useEffect` 管理地图实例生命周期

```jsx
useEffect(() => {
  window.require([
    'esri/Map',
    'esri/views/MapView',
    'esri/layers/WebTileLayer'
  ], (Map, MapView, WebTileLayer) => {
    // 初始化地图
  })

  return () => {
    // 清理
    view.destroy()
  }
}, [])
```

---

## 5. 算法模块

### 5.1 KNN-DTW 检测器

位置：`backend/runners/algorithm/knndtw_detector.py`

核心算法流程：
1. 读取 NDVI 时间序列和裸煤概率数据
2. 提取裸煤区域（概率 > 阈值）
3. 使用 DTW 距离计算 NDVI 曲线相似度
4. KNN 分类识别扰动类型
5. 输出检测结果栅格

### 5.2 运行器模式

```
base_runner.py (抽象基类)
      │
      ├── python_runner.py (Python 实现)
      │
      └── (可扩展其他引擎)
```

---

## 6. 数据流

### 6.1 检测任务流程

```
用户上传文件
      │
      ▼
  ┌─────────────────┐
  │ POST /api/upload │ → 保存到 data/uploads/{job_id}/
  └─────────────────┘
      │
      ▼
  ┌─────────────────┐
  │ POST /api/run    │ → 调用 PythonRunner
  └─────────────────┘
      │
      ▼
  ┌─────────────────┐
  │ 算法执行         │ → 输出到 data/jobs/{job_id}/
  └─────────────────┘
      │
      ▼
  返回 bounds + crs_info
      │
      ▼
  前端加载地图图层
```

### 6.2 瓦片请求流程

```
GET /api/tiles/{layer}/{z}/{x}/{y}
      │
      ▼
  检查缓存
      │
      ├── 命中 → 返回缓存
      │
      └── 未命中 → 渲染瓦片 → 缓存 → 返回
```

---

## 7. 安全设计

### 7.1 认证安全
- 密码使用 `werkzeug.security` 哈希存储
- JWT 签名使用 HS256 算法
- Access Token 有效期 2 小时
- Refresh Token 有效期 30 天

### 7.2 访问控制
- `@jwt_required`: 需要有效的 access_token
- `@admin_required`: 需要 admin 角色
- 用户只能访问自己的任务数据

### 7.3 输入验证
- 文件类型检查（仅接受 .tif/.tiff）
- 文件大小限制
- API 参数验证

---

## 8. 扩展性设计

### 8.1 算法扩展
- 实现新的 Runner 类继承 `BaseRunner`
- 在 `job_routes.py` 中注册新引擎

### 8.2 数据库扩展
- SQLAlchemy ORM 支持迁移到其他数据库
- 修改 `config.py` 中的 `DATABASE_URI`

### 8.3 前端扩展
- 组件化设计便于复用
- 路由配置集中管理
