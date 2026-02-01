# 矿区检测平台 - 部署指南

## 1. 环境要求

### 1.1 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+), macOS, Windows
- **Python**: 3.9 - 3.11
- **Node.js**: 18+ (仅构建前端需要)
- **内存**: 最低 4GB, 推荐 8GB+
- **磁盘**: 10GB+ (根据数据量调整)

### 1.2 Python 依赖
主要依赖包：
- Flask 3.x
- SQLAlchemy
- PyJWT
- Rasterio (需要 GDAL)
- NumPy, Scikit-learn

---

## 2. 快速部署

### 2.1 克隆/下载项目

```bash
# 假设项目已下载到本地
cd /path/to/mining_platform
```

### 2.2 安装 Python 依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2.3 初始化数据库

```bash
python init_db.py
```

输出应包含：
```
数据库表已创建
管理员账户已创建: admin / admin123
```

### 2.4 构建前端（如需修改）

```bash
cd ../frontend
npm install
npm run build
```

### 2.5 启动服务

```bash
cd ../backend
python app.py
```

访问 http://localhost:5000

---

## 3. 生产环境部署

### 3.1 使用 Gunicorn (Linux/macOS)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

参数说明：
- `-w 4`: 4 个工作进程
- `-b 0.0.0.0:5000`: 绑定地址和端口

### 3.2 Systemd 服务配置

创建 `/etc/systemd/system/mining-platform.service`:

```ini
[Unit]
Description=Mining Detection Platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/mining_platform/backend
Environment="PATH=/opt/mining_platform/backend/venv/bin"
ExecStart=/opt/mining_platform/backend/venv/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:5000 \
    "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mining-platform
sudo systemctl start mining-platform
```

### 3.3 Nginx 反向代理

创建 `/etc/nginx/sites-available/mining-platform`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /opt/mining_platform/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 文件上传大小限制
        client_max_body_size 500M;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/mining-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3.4 HTTPS 配置 (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 4. 环境变量配置

### 4.1 关键配置项

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | JWT 签名密钥 | 随机生成 |
| DATABASE_URI | 数据库连接 | sqlite:///data/mining.db |
| UPLOAD_FOLDER | 上传目录 | ../data/uploads |
| JOBS_FOLDER | 任务目录 | ../data/jobs |
| ACCESS_TOKEN_EXPIRE | Access Token 有效期(秒) | 7200 |
| REFRESH_TOKEN_EXPIRE | Refresh Token 有效期(秒) | 2592000 |

### 4.2 设置方式

**方式一**: 环境变量
```bash
export SECRET_KEY="your-secure-key-here"
export DATABASE_URI="postgresql://user:pass@localhost/mining"
```

**方式二**: 修改 config.py
```python
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secure-key-here")
    ...
```

---

## 5. GDAL 安装

Rasterio 依赖 GDAL，需要先安装系统库。

### 5.1 Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y gdal-bin libgdal-dev
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"
pip install rasterio
```

### 5.2 macOS (Homebrew)

```bash
brew install gdal
pip install rasterio
```

### 5.3 Windows

推荐使用 conda:
```bash
conda install -c conda-forge rasterio
```

或从 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 下载预编译 wheel。

---

## 6. Docker 部署（可选）

### 6.1 Dockerfile

```dockerfile
FROM python:3.10-slim

# 安装 GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/
COPY data/ ./data/

WORKDIR /app/backend

# 初始化数据库
RUN python init_db.py

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

### 6.2 docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=your-secret-key
    restart: unless-stopped
```

### 6.3 构建与运行

```bash
docker-compose up -d --build
```

---

## 7. 数据目录结构

```
data/
├── mining.db           # SQLite 数据库
├── uploads/            # 用户上传文件
│   └── {job_id}/       # 每个任务一个目录
│       ├── ndvi.tif
│       └── coal.tif
└── jobs/               # 任务输出文件
    └── {job_id}/
        ├── result.tif
        ├── result.geojson
        └── tiles/      # 瓦片缓存
```

确保 Web 服务用户有读写权限：
```bash
sudo chown -R www-data:www-data /opt/mining_platform/data
sudo chmod -R 755 /opt/mining_platform/data
```

---

## 8. 监控与日志

### 8.1 Gunicorn 日志

```bash
gunicorn -w 4 -b 0.0.0.0:5000 \
    --access-logfile /var/log/mining/access.log \
    --error-logfile /var/log/mining/error.log \
    "app:create_app()"
```

### 8.2 Systemd 日志

```bash
sudo journalctl -u mining-platform -f
```

### 8.3 应用日志

在 `app.py` 中配置 Python logging：
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
```

---

## 9. 备份策略

### 9.1 数据库备份

```bash
# 每日备份
cp /opt/mining_platform/data/mining.db \
   /backup/mining_$(date +%Y%m%d).db

# 保留最近 7 天
find /backup -name "mining_*.db" -mtime +7 -delete
```

### 9.2 文件备份

```bash
# 使用 rsync 增量备份
rsync -av /opt/mining_platform/data/ /backup/mining_data/
```

---

## 10. 故障排除

### 10.1 常见问题

**问题**: `ModuleNotFoundError: No module named 'rasterio'`
**解决**: 安装 GDAL 后重新安装 rasterio

**问题**: 上传文件失败 413
**解决**: 调整 Nginx `client_max_body_size`

**问题**: 瓦片加载缓慢
**解决**: 检查磁盘 I/O，考虑使用 SSD 或增加瓦片缓存

### 10.2 健康检查

```bash
# 检查服务状态
curl http://localhost:5000/api/auth/login -X POST -d '{}' -H "Content-Type: application/json"
# 应返回 400 (参数错误) 而非 500

# 检查数据库
sqlite3 /opt/mining_platform/data/mining.db "SELECT COUNT(*) FROM users;"
```
