# 露天矿区扰动检测平台 - 技术图表集

> 本文档包含系统的各类技术图表，使用 Mermaid 格式编写
> 可在支持 Mermaid 的编辑器（如 Typora、VS Code + 插件、GitHub）中渲染

---

## 1. 数据库 ER 图

```mermaid
erDiagram
    USERS ||--o{ JOBS : "创建"
    JOBS ||--o{ JOB_FILES : "包含"

    USERS {
        int id PK "主键"
        string username UK "用户名(唯一)"
        string email UK "邮箱(唯一)"
        string password_hash "密码哈希"
        string role "角色: user/admin"
        boolean is_active "账户状态"
        datetime created_at "注册时间"
        datetime last_login "最后登录"
    }

    JOBS {
        int id PK "主键"
        string job_id UK "任务UUID"
        int user_id FK "用户外键"
        string status "状态: pending/running/completed/failed"
        string engine "算法引擎"
        int startyear "起始年份"
        string ndvi_filename "NDVI文件名"
        string coal_filename "裸煤文件名"
        text bounds_json "地理边界JSON"
        text crs_info_json "坐标系信息JSON"
        text error_message "错误信息"
        datetime created_at "创建时间"
        datetime completed_at "完成时间"
    }

    JOB_FILES {
        int id PK "主键"
        int job_db_id FK "任务外键"
        string filename "文件名"
        string label "显示标签"
        string file_type "类型: input/output"
        int size "文件大小(bytes)"
    }
```

---

## 2. 系统架构图

```mermaid
flowchart TB
    subgraph Client["客户端层"]
        Browser["Web 浏览器"]
        subgraph Frontend["React 前端"]
            React["React 18 + Vite 5"]
            Zustand["Zustand 状态管理"]
            ArcGIS["ArcGIS Maps SDK 4.29"]
            ChartJS["Chart.js 图表"]
        end
    end

    subgraph Server["服务端层"]
        subgraph Flask["Flask 3.0 应用"]
            AuthBP["认证蓝图\n/api/auth/*"]
            JobBP["任务蓝图\n/api/*"]
            TileBP["瓦片蓝图\n/api/tiles/*"]
            AdminBP["管理蓝图\n/api/admin/*"]
        end

        subgraph Services["服务层"]
            GeoService["地理处理服务\ngeo_service.py"]
            TileService["瓦片渲染服务\ntile_service.py"]
        end

        subgraph Algorithm["算法引擎"]
            PythonRunner["Python 检测引擎"]
            subgraph Core["核心算法"]
                DTW["DTW 动态时间规整\n(Numba JIT 加速)"]
                BWlvbo["BWlvbo 时序平滑\n(小波去噪)"]
                KNN["KNN-DTW 分类器\n(49 模板匹配)"]
                Sample["模板生成器\n(creat_sample)"]
            end
        end
    end

    subgraph Data["数据层"]
        SQLite["SQLite 数据库\nmining.db"]
        Uploads["上传目录\n/data/uploads/"]
        Jobs["结果目录\n/data/jobs/"]
    end

    Browser <--> React
    React <--> Flask
    Flask <--> Services
    Flask <--> Algorithm
    Services <--> Data
    Algorithm <--> Data
```

---

## 3. 用户认证时序图

```mermaid
sequenceDiagram
    participant U as 用户浏览器
    participant F as React 前端
    participant A as Flask /api/auth
    participant D as SQLite 数据库

    Note over U,D: 用户登录流程

    U->>F: 输入用户名/密码
    F->>A: POST /api/auth/login
    A->>D: 查询用户记录
    D-->>A: 返回用户数据
    A->>A: 验证密码哈希
    A->>A: 生成 JWT Token
    A-->>F: {access_token, refresh_token, user}
    F->>F: 存储到 localStorage
    F-->>U: 跳转到检测页面

    Note over U,D: Token 自动刷新流程

    U->>F: 发起 API 请求
    F->>A: GET /api/jobs (携带过期Token)
    A-->>F: 401 Unauthorized
    F->>A: POST /api/auth/refresh
    A->>A: 验证 refresh_token
    A-->>F: {new_access_token}
    F->>F: 更新 localStorage
    F->>A: 重试原请求 (新Token)
    A-->>F: 返回数据
    F-->>U: 显示结果
```

---

## 4. 检测任务处理时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as React 前端
    participant J as Flask /api
    participant R as PythonRunner
    participant DB as SQLite
    participant FS as 文件系统

    Note over U,FS: 文件上传阶段

    U->>F: 选择 NDVI GeoTIFF
    F->>J: POST /api/upload (file, kind=ndvi)
    J->>DB: 创建 Job 记录 (status=pending)
    J->>FS: 保存到 /data/uploads/{job_id}/
    J-->>F: {job_id, filename}

    U->>F: 选择裸煤概率 GeoTIFF
    F->>J: POST /api/upload (file, kind=coal, job_id)
    J->>FS: 保存到 /data/uploads/{job_id}/
    J-->>F: {job_id, filename}

    Note over U,FS: 检测执行阶段

    U->>F: 点击"运行检测"
    F->>J: POST /api/run {job_id, startyear}
    J->>DB: 更新 status=running
    J->>R: run_detect(ndvi, coal, out_dir, startyear)

    activate R
    R->>R: Step 1: 加载 NDVI 数据
    R->>R: Step 2: 数据清洗与归一化
    R->>R: Step 3: 生成 49 个训练模板
    R->>R: Step 4: KNN-DTW 分类 (并行处理)
    R->>R: Step 5: 空间滤波 (形态学开运算)
    R->>R: Step 6: 裸煤概率验证
    R->>R: Step 7: 输出 GeoTIFF 结果
    R->>FS: 写入 7 个输出文件
    R-->>J: 返回 {outputs, bounds, crs_info}
    deactivate R

    J->>DB: 更新 status=completed, bounds, crs_info
    J->>DB: 插入 JobFile 记录
    J-->>F: {job_id, bounds, crs_info, outputs}

    Note over U,FS: 结果可视化阶段

    F->>F: 地图飞行到 bounds
    F->>J: GET /api/tiles/{job_id}/disturbance_mask/{z}/{x}/{y}.png
    J->>FS: 读取 GeoTIFF
    J->>J: 渲染瓦片 (重投影+着色)
    J-->>F: PNG 图像
    F-->>U: 显示检测结果
```

---

## 5. KNN-DTW 算法流程图

```mermaid
flowchart TB
    subgraph Input["输入数据"]
        NDVI["NDVI 多波段 GeoTIFF\n(m × n × l 像元)"]
        Coal["裸煤概率 GeoTIFF"]
    end

    subgraph Preprocess["预处理"]
        Clean["数据清洗\n零值→NaN\n异常值处理"]
        Norm["归一化\n计算0.5/99.5百分位"]
        Reshape["重塑为像元序列\n(m×n, l)"]
    end

    subgraph Template["模板生成"]
        Sample["creat_sample(s, l, 0.8, 0.6)"]
        T49["49 个模板\n• 1-9: 仅扰动\n• 10-36: 扰动+恢复\n• 37-40: 稳定\n• 41-49: 仅恢复"]
    end

    subgraph Classification["KNN-DTW 分类"]
        direction TB
        Loop["遍历每个有效像元"]
        NaN["移除 NaN\n记录位置"]
        BWlvbo["BWlvbo 平滑\n• 尖峰移除\n• 小波去噪"]
        DTW["DTW 距离计算\n(与49个模板)"]
        Best["选择最近邻模板"]
        Path["计算弯曲路径"]
        Year["提取扰动/恢复年份"]
    end

    subgraph Spatial["空间滤波"]
        Morph["形态学开运算\ndisk r=2"]
        Label["连通区域标记\n8-邻域"]
    end

    subgraph Validate["裸煤验证"]
        Resample["重采样裸煤数据"]
        Filter["筛选条件:\n• total ≥ 1111\n• union ≥ 222\n• ratio ≥ 0.02"]
    end

    subgraph Output["输出文件"]
        Mask["mining_disturbance_mask.tif\n扰动掩膜"]
        DYear["mining_disturbance_year.tif\n扰动年份"]
        RYear["mining_recovery_year.tif\n恢复年份"]
        Potential["potential_disturbance.tif\n潜在扰动"]
        Type["res_disturbance_type.tif\n扰动类型"]
    end

    NDVI --> Clean --> Norm --> Reshape
    Coal --> Validate
    Norm --> Sample --> T49

    Reshape --> Loop
    Loop --> NaN --> BWlvbo --> DTW
    T49 --> DTW
    DTW --> Best --> Path --> Year
    Year --> Loop

    Loop --> Morph --> Label --> Validate
    Validate --> Filter --> Output
```

---

## 6. DTW 动态时间规整原理图

```mermaid
flowchart LR
    subgraph Concept["DTW 核心概念"]
        R["参考序列 R\n(模板)"]
        T["测试序列 T\n(像元NDVI)"]
        D["累积距离矩阵 D"]
        W["弯曲路径 W"]
    end

    subgraph Formula["递推公式"]
        F["D(i,j) = d(rᵢ,tⱼ) + min{\nD(i-1,j)\nD(i-1,j-1)\nD(i,j-1)\n}"]
    end

    subgraph Path["路径回溯"]
        P1["从 D(M,N) 开始"]
        P2["选择最小邻居"]
        P3["优先级: 上 > 左 > 对角"]
        P4["返回到 D(1,1)"]
    end

    R --> D
    T --> D
    D --> F
    F --> W
    W --> Path
```

---

## 7. 49 模板分类图

```mermaid
flowchart TB
    subgraph Templates["49 个 NDVI 时序模板"]
        subgraph Dist["仅扰动 (1-9)"]
            D1["1,2,3: 100%振幅\n@25%/50%/75%"]
            D2["4,5,6: 80%振幅\n@25%/50%/75%"]
            D3["7,8,9: 60%振幅\n@25%/50%/75%"]
        end

        subgraph DistRec["扰动+恢复 (10-36)"]
            DR1["10-12: 100%扰动→100%恢复"]
            DR2["13-15: 80%扰动→100%恢复"]
            DR3["16-36: 各种振幅组合"]
        end

        subgraph Stable["稳定 (37-40)"]
            S1["37: 稳定低值 (已扰动)"]
            S2["38-40: 稳定高值 (健康)"]
        end

        subgraph Rec["仅恢复 (41-49)"]
            R1["41-43: 恢复→100%"]
            R2["44-46: 恢复→80%"]
            R3["47-49: 恢复→60%"]
        end
    end

    subgraph Curve["典型 NDVI 曲线形状"]
        C1["━━━╲____\n仅扰动"]
        C2["━━╲__╱━━\n扰动+恢复"]
        C3["━━━━━━━\n稳定"]
        C4["____╱━━━\n仅恢复"]
    end

    Dist --> C1
    DistRec --> C2
    Stable --> C3
    Rec --> C4
```

---

## 8. 系统部署架构图

```mermaid
flowchart TB
    subgraph Production["生产环境部署"]
        subgraph Client["客户端"]
            Browser["浏览器"]
        end

        subgraph Server["服务器"]
            Nginx["Nginx\n反向代理 + 静态文件"]
            Gunicorn["Gunicorn\n4 Workers"]
            Flask["Flask App"]
        end

        subgraph Storage["存储"]
            SQLite["SQLite DB"]
            FileSystem["文件系统\n/data/"]
        end
    end

    Browser -->|HTTPS:443| Nginx
    Nginx -->|静态文件| Browser
    Nginx -->|/api/*| Gunicorn
    Gunicorn --> Flask
    Flask --> SQLite
    Flask --> FileSystem
```

---

## 9. 数据流图 (DFD)

```mermaid
flowchart LR
    subgraph External["外部实体"]
        User["用户"]
        GeoData["遥感数据源"]
    end

    subgraph Process["处理过程"]
        P1["1.0\n用户认证"]
        P2["2.0\n文件上传"]
        P3["3.0\n扰动检测"]
        P4["4.0\n结果可视化"]
        P5["5.0\n数据导出"]
    end

    subgraph Store["数据存储"]
        D1["用户表"]
        D2["任务表"]
        D3["文件存储"]
    end

    User -->|登录信息| P1
    P1 -->|JWT Token| User
    P1 <-->|验证| D1

    GeoData -->|GeoTIFF| User
    User -->|上传文件| P2
    P2 -->|保存| D3
    P2 -->|创建任务| D2

    User -->|执行检测| P3
    P3 -->|读取| D3
    P3 -->|更新状态| D2
    P3 -->|输出结果| D3

    User -->|查看地图| P4
    P4 -->|读取结果| D3
    P4 -->|瓦片/GeoJSON| User

    User -->|下载| P5
    P5 -->|读取| D3
    P5 -->|ZIP文件| User
```

---

## 10. 状态机图 - 任务状态流转

```mermaid
stateDiagram-v2
    [*] --> pending: 创建任务

    pending --> running: 开始执行
    pending --> failed: 参数错误

    running --> completed: 检测成功
    running --> failed: 检测失败

    completed --> [*]: 用户删除
    failed --> [*]: 用户删除

    note right of pending: 等待用户上传文件\n或点击执行
    note right of running: 算法正在处理\n(可能需要数分钟)
    note right of completed: 结果可查看/下载
    note right of failed: 显示错误信息
```

---

## 11. API 接口关系图

```mermaid
flowchart TB
    subgraph Auth["/api/auth"]
        A1["POST /register\n用户注册"]
        A2["POST /login\n用户登录"]
        A3["POST /refresh\nToken刷新"]
    end

    subgraph User["/api/user"]
        U1["GET /profile\n获取个人信息"]
        U2["PUT /profile\n更新个人信息"]
        U3["PUT /password\n修改密码"]
    end

    subgraph Job["/api"]
        J1["POST /upload\n上传文件"]
        J2["POST /run\n执行检测"]
        J3["GET /jobs\n任务列表"]
        J4["GET /jobs/:id\n任务详情"]
        J5["DELETE /jobs/:id\n删除任务"]
        J6["GET /ndvi-timeseries\nNDVI时序查询"]
        J7["GET /job-files/:id\n文件列表"]
        J8["POST /download-zip/:id\n打包下载"]
    end

    subgraph Tile["/api"]
        T1["GET /tiles/:job/:layer/:z/:x/:y.png\n动态瓦片"]
        T2["GET /result-geojson/:job/:layer\n矢量数据"]
    end

    subgraph Admin["/api/admin"]
        AD1["GET /stats\n系统统计"]
        AD2["GET /users\n用户列表"]
        AD3["PUT /users/:id\n修改用户"]
        AD4["DELETE /users/:id\n删除用户"]
        AD5["GET /jobs\n所有任务"]
        AD6["DELETE /jobs/:id\n删除任务"]
    end

    A2 -->|返回Token| J1
    J1 -->|job_id| J2
    J2 -->|bounds| T1
    J2 -->|bounds| T2
```

---

## 图表导出说明

### 方法1: 使用 Mermaid Live Editor
1. 访问 https://mermaid.live/
2. 复制上述 Mermaid 代码
3. 导出为 PNG/SVG

### 方法2: 使用 VS Code
1. 安装插件 "Markdown Preview Mermaid Support"
2. 打开此文件预览
3. 右键导出图片

### 方法3: 使用 Typora
1. 用 Typora 打开此 Markdown 文件
2. 文件 → 导出 → PDF 或图片

### 方法4: GitHub 渲染
1. 将此文件推送到 GitHub
2. 在 GitHub 上查看会自动渲染 Mermaid 图表

---

**文档版本**: 1.0.0
**最后更新**: 2026年2月1日
