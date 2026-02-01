# 矿区检测平台 - API 接口文档

## 基础信息

- **Base URL**: `http://localhost:5000/api`
- **认证方式**: JWT Bearer Token
- **响应格式**: JSON

---

## 1. 认证接口

### 1.1 用户注册

```http
POST /api/auth/register
Content-Type: application/json
```

**请求体**
```json
{
  "username": "string (2-80字符)",
  "email": "string (有效邮箱)",
  "password": "string (至少6字符)"
}
```

**成功响应** `201 Created`
```json
{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user"
  }
}
```

**错误响应**
| 状态码 | 错误 |
|--------|------|
| 400 | 缺少必填字段 / 用户名或邮箱已存在 |

---

### 1.2 用户登录

```http
POST /api/auth/login
Content-Type: application/json
```

**请求体**
```json
{
  "username": "string",
  "password": "string"
}
```

**成功响应** `200 OK`
```json
{
  "message": "登录成功",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

**错误响应**
| 状态码 | 错误 |
|--------|------|
| 401 | 用户名或密码错误 |
| 403 | 账户已被禁用 |

---

### 1.3 刷新 Token

```http
POST /api/auth/refresh
Content-Type: application/json
```

**请求体**
```json
{
  "refresh_token": "eyJ..."
}
```

**成功响应** `200 OK`
```json
{
  "access_token": "eyJ..."
}
```

---

## 2. 用户接口

> 以下接口均需要 `Authorization: Bearer <access_token>` 头

### 2.1 获取个人信息

```http
GET /api/user/profile
Authorization: Bearer <token>
```

**响应**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00",
    "last_login": "2024-01-02T08:00:00"
  }
}
```

---

### 2.2 更新个人信息

```http
PUT /api/user/profile
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**
```json
{
  "email": "newemail@example.com"
}
```

**响应**
```json
{
  "message": "更新成功",
  "user": { ... }
}
```

---

### 2.3 修改密码

```http
PUT /api/user/password
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**
```json
{
  "old_password": "string",
  "new_password": "string (至少6字符)"
}
```

**响应**
```json
{
  "message": "密码修改成功"
}
```

---

## 3. 检测任务接口

### 3.1 上传文件

```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**表单字段**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | GeoTIFF 文件 (.tif/.tiff) |
| kind | string | 是 | 文件类型: `ndvi` 或 `coal` |
| job_id | string | 否 | 已有任务ID（上传第二个文件时） |

**响应**
```json
{
  "message": "上传成功",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "ndvi_timeseries.tif"
}
```

---

### 3.2 运行检测

```http
POST /api/run
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "startyear": 2010,
  "engine": "python"
}
```

**响应**
```json
{
  "message": "检测完成",
  "job_id": "550e8400-...",
  "bounds": {
    "west": 116.0,
    "south": 39.0,
    "east": 117.0,
    "north": 40.0
  },
  "crs_info": {
    "epsg": 4326,
    "crs_string": "EPSG:4326",
    "warning": null
  }
}
```

---

### 3.3 获取 NDVI 时间序列

```http
GET /api/ndvi-timeseries
Authorization: Bearer <token>
```

**查询参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| job_id | string | 是 | 任务ID |
| lon | float | 是 | 经度 (WGS84) |
| lat | float | 是 | 纬度 (WGS84) |
| startyear | int | 否 | 起始年份 (默认2010) |

**响应**
```json
{
  "lon": 116.5,
  "lat": 39.5,
  "years": [2010, 2011, 2012, ...],
  "ndvi_values": [0.65, 0.68, 0.62, ...],
  "result_value": 1,
  "coal_prob": 0.85
}
```

---

### 3.4 获取任务列表（历史记录）

```http
GET /api/jobs
Authorization: Bearer <token>
```

**查询参数**
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| page | int | 1 | 页码 |
| per_page | int | 10 | 每页数量 |

**响应**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-...",
      "status": "completed",
      "engine": "python",
      "startyear": 2010,
      "ndvi_filename": "ndvi.tif",
      "coal_filename": "coal.tif",
      "created_at": "2024-01-01T12:00:00",
      "completed_at": "2024-01-01T12:05:00"
    }
  ],
  "total": 25,
  "pages": 3,
  "current_page": 1
}
```

---

### 3.5 获取任务详情

```http
GET /api/jobs/{job_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "job": {
    "job_id": "550e8400-...",
    "status": "completed",
    "bounds": { ... },
    "crs_info": { ... },
    ...
  }
}
```

---

### 3.6 删除任务

```http
DELETE /api/jobs/{job_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "message": "任务已删除"
}
```

---

### 3.7 获取任务文件列表

```http
GET /api/job-files/{job_id}
Authorization: Bearer <token>
```

**响应**
```json
{
  "files": [
    {
      "filename": "result.tif",
      "label": "检测结果栅格",
      "file_type": "output",
      "size": 1234567
    }
  ]
}
```

---

### 3.8 下载文件（ZIP打包）

```http
POST /api/download-zip/{job_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**
```json
{
  "files": ["result.tif", "ndvi_mosaic.tif"]
}
```

**响应**: ZIP 文件流

---

## 4. 瓦片服务接口

### 4.1 获取地图瓦片

```http
GET /api/tiles/{layer}/{z}/{x}/{y}
```

**路径参数**
| 参数 | 说明 |
|------|------|
| layer | 图层名称，格式: `{job_id}_{type}` |
| z | 缩放级别 |
| x | 瓦片列号 |
| y | 瓦片行号 |

**图层类型**
- `{job_id}_result`: 检测结果
- `{job_id}_ndvi_{band}`: NDVI 某一波段
- `{job_id}_coal`: 裸煤概率

**响应**: PNG 图片

---

### 4.2 获取 GeoJSON 边界

```http
GET /api/result-geojson/{job_id}
```

**响应**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { ... },
      "properties": { "value": 1 }
    }
  ]
}
```

---

## 5. 管理员接口

> 需要 admin 角色

### 5.1 获取统计信息

```http
GET /api/admin/stats
Authorization: Bearer <admin_token>
```

**响应**
```json
{
  "user_count": 100,
  "job_count": 500,
  "completed_jobs": 450,
  "disk_usage": 1073741824,
  "upload_dir": "/path/to/uploads",
  "jobs_dir": "/path/to/jobs",
  "recent_jobs": [ ... ]
}
```

---

### 5.2 获取用户列表

```http
GET /api/admin/users
Authorization: Bearer <admin_token>
```

**响应**
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true,
      "created_at": "...",
      "last_login": "..."
    }
  ]
}
```

---

### 5.3 修改用户

```http
PUT /api/admin/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**请求体**
```json
{
  "role": "admin",
  "is_active": true
}
```

---

### 5.4 删除用户

```http
DELETE /api/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

---

### 5.5 获取所有任务

```http
GET /api/admin/jobs
Authorization: Bearer <admin_token>
```

**查询参数**
| 参数 | 说明 |
|------|------|
| page | 页码 |
| per_page | 每页数量 |
| status | 状态过滤 |
| username | 用户名过滤 |

---

### 5.6 删除任意任务

```http
DELETE /api/admin/jobs/{job_id}
Authorization: Bearer <admin_token>
```

---

## 错误响应格式

所有错误响应遵循以下格式：

```json
{
  "error": "错误描述信息"
}
```

## 通用状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 / Token 无效 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
