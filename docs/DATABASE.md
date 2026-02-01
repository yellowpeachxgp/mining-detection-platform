# 矿区检测平台 - 数据库设计文档

## 1. 概述

- **数据库类型**: SQLite
- **ORM**: SQLAlchemy
- **数据库文件**: `data/mining.db`

---

## 2. 数据表结构

### 2.1 users 表 - 用户信息

存储系统用户账户信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 主键 |
| username | VARCHAR(80) | UNIQUE, NOT NULL, INDEX | 用户名 |
| email | VARCHAR(120) | UNIQUE, NOT NULL, INDEX | 邮箱地址 |
| password_hash | VARCHAR(256) | NOT NULL | 密码哈希 (werkzeug) |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'user' | 角色: 'user' / 'admin' |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 账户是否启用 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 注册时间 |
| last_login | DATETIME | NULL | 最后登录时间 |

**索引**
- `ix_users_username` (username)
- `ix_users_email` (email)

**示例数据**
```sql
INSERT INTO users (username, email, password_hash, role)
VALUES ('admin', 'admin@example.com', 'pbkdf2:sha256:...', 'admin');
```

---

### 2.2 jobs 表 - 检测任务

存储用户提交的检测任务信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 主键 |
| job_id | VARCHAR(36) | UNIQUE, NOT NULL, INDEX | UUID 任务标识 |
| user_id | INTEGER | FOREIGN KEY → users.id, INDEX | 所属用户 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | 状态 |
| engine | VARCHAR(20) | DEFAULT 'python' | 算法引擎 |
| startyear | INTEGER | NULL | NDVI 起始年份 |
| ndvi_filename | VARCHAR(255) | NULL | 原始 NDVI 文件名 |
| coal_filename | VARCHAR(255) | NULL | 原始裸煤文件名 |
| bounds_json | TEXT | NULL | 边界 JSON |
| crs_info_json | TEXT | NULL | 坐标系信息 JSON |
| error_message | TEXT | NULL | 错误信息 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |
| completed_at | DATETIME | NULL | 完成时间 |

**状态值**
| 状态 | 说明 |
|------|------|
| pending | 等待处理 |
| running | 正在运行 |
| completed | 已完成 |
| failed | 失败 |

**外键关系**
```
jobs.user_id → users.id (ON DELETE CASCADE)
```

**bounds_json 示例**
```json
{
  "west": 116.0,
  "south": 39.0,
  "east": 117.0,
  "north": 40.0
}
```

**crs_info_json 示例**
```json
{
  "epsg": 4326,
  "crs_string": "EPSG:4326",
  "warning": null
}
```

---

### 2.3 job_files 表 - 任务文件

存储与任务关联的输入/输出文件信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 主键 |
| job_id | INTEGER | FOREIGN KEY → jobs.id | 所属任务 |
| filename | VARCHAR(255) | NOT NULL | 文件名 |
| label | VARCHAR(100) | NULL | 中文标签 |
| file_type | VARCHAR(20) | NOT NULL | 类型: 'input' / 'output' |
| size | INTEGER | NULL | 文件大小 (bytes) |

**外键关系**
```
job_files.job_id → jobs.id (ON DELETE CASCADE)
```

**常见文件标签**
| 文件名模式 | 标签 | 类型 |
|------------|------|------|
| *ndvi*.tif | NDVI时序数据 | input |
| *coal*.tif | 裸煤概率数据 | input |
| result.tif | 检测结果栅格 | output |
| result.geojson | 检测结果矢量 | output |

---

## 3. ER 图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   users     │       │    jobs     │       │  job_files  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │──┐    │ id (PK)     │
│ username    │  │    │ job_id      │  │    │ job_id (FK) │──┘
│ email       │  └───>│ user_id(FK) │  └───>│ filename    │
│ password_h  │       │ status      │       │ label       │
│ role        │       │ engine      │       │ file_type   │
│ is_active   │       │ startyear   │       │ size        │
│ created_at  │       │ bounds_json │       └─────────────┘
│ last_login  │       │ crs_info_j  │
└─────────────┘       │ error_msg   │
                      │ created_at  │
                      │ completed_at│
                      └─────────────┘
```

---

## 4. SQLAlchemy 模型

### 4.1 User 模型

```python
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # 关联
    jobs = db.relationship("Job", backref="owner", lazy="dynamic",
                          cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
```

### 4.2 Job 模型

```python
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    engine = db.Column(db.String(20), default="python")
    startyear = db.Column(db.Integer, nullable=True)
    ndvi_filename = db.Column(db.String(255), nullable=True)
    coal_filename = db.Column(db.String(255), nullable=True)
    bounds_json = db.Column(db.Text, nullable=True)
    crs_info_json = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # 关联
    files = db.relationship("JobFile", backref="job", lazy="dynamic",
                           cascade="all, delete-orphan")

    @property
    def bounds(self):
        return json.loads(self.bounds_json) if self.bounds_json else None

    @bounds.setter
    def bounds(self, value):
        self.bounds_json = json.dumps(value) if value else None
```

### 4.3 JobFile 模型

```python
class JobFile(db.Model):
    __tablename__ = "job_files"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(100), nullable=True)
    file_type = db.Column(db.String(20), nullable=False)  # input / output
    size = db.Column(db.Integer, nullable=True)
```

---

## 5. 数据库初始化

### 5.1 初始化脚本

运行 `init_db.py` 进行初始化：

```bash
cd backend
python init_db.py
```

脚本执行内容：
1. 创建所有表
2. 创建默认管理员账户 (admin / admin123)

### 5.2 手动初始化

```python
from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    db.create_all()

    # 创建管理员
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
```

---

## 6. 常用查询示例

### 6.1 查询用户的所有任务

```python
user = User.query.filter_by(username='testuser').first()
jobs = user.jobs.order_by(Job.created_at.desc()).all()
```

### 6.2 分页查询

```python
page = 1
per_page = 10
pagination = Job.query.filter_by(user_id=user_id)\
    .order_by(Job.created_at.desc())\
    .paginate(page=page, per_page=per_page, error_out=False)

jobs = pagination.items
total_pages = pagination.pages
```

### 6.3 统计查询

```python
from sqlalchemy import func

# 用户总数
user_count = User.query.count()

# 各状态任务数
status_counts = db.session.query(
    Job.status, func.count(Job.id)
).group_by(Job.status).all()
```

### 6.4 级联删除

删除用户时自动删除其所有任务：

```python
user = User.query.get(user_id)
db.session.delete(user)
db.session.commit()  # jobs 和 job_files 会自动删除
```

---

## 7. 数据备份与迁移

### 7.1 备份

```bash
cp data/mining.db data/mining_backup_$(date +%Y%m%d).db
```

### 7.2 迁移到 PostgreSQL

1. 修改 `config.py`:
```python
DATABASE_URI = "postgresql://user:pass@localhost/mining"
```

2. 安装驱动:
```bash
pip install psycopg2-binary
```

3. 重新初始化:
```bash
python init_db.py
```

### 7.3 数据导出

```bash
sqlite3 data/mining.db .dump > backup.sql
```
