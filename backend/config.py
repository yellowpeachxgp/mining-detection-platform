import os
import secrets

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
JOB_DIR = os.path.join(DATA_DIR, "jobs")

MATLAB_DIR = os.path.join(BASE_DIR, "matlab")

# Detection engine: 'python' (default, no MATLAB needed) or 'matlab'
DETECTION_ENGINE = os.environ.get('DETECTION_ENGINE', 'python')

# ============= 数据库配置 =============
DATABASE_URI = os.environ.get('DATABASE_URI', f"sqlite:///{os.path.join(DATA_DIR, 'mining.db')}")

# ============= JWT 配置 =============
# 生产环境应通过环境变量设置
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
ACCESS_TOKEN_EXPIRE = int(os.environ.get('ACCESS_TOKEN_EXPIRE', 2))  # 小时
REFRESH_TOKEN_EXPIRE = int(os.environ.get('REFRESH_TOKEN_EXPIRE', 30))  # 天

# ============= 默认管理员账户 =============
DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@mining.local')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
