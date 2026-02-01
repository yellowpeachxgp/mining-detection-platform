"""SQLAlchemy 数据库模型"""
import json
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' / 'admin'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    jobs = db.relationship("Job", backref="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending/running/completed/failed
    engine = db.Column(db.String(20), nullable=True)
    startyear = db.Column(db.Integer, nullable=True)
    ndvi_filename = db.Column(db.String(255), nullable=True)
    coal_filename = db.Column(db.String(255), nullable=True)
    bounds_json = db.Column(db.Text, nullable=True)
    crs_info_json = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    files = db.relationship("JobFile", backref="job", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def bounds(self):
        if self.bounds_json:
            return json.loads(self.bounds_json)
        return None

    @bounds.setter
    def bounds(self, value):
        self.bounds_json = json.dumps(value) if value else None

    @property
    def crs_info(self):
        if self.crs_info_json:
            return json.loads(self.crs_info_json)
        return None

    @crs_info.setter
    def crs_info(self, value):
        self.crs_info_json = json.dumps(value) if value else None

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "status": self.status,
            "engine": self.engine,
            "startyear": self.startyear,
            "ndvi_filename": self.ndvi_filename,
            "coal_filename": self.coal_filename,
            "bounds": self.bounds,
            "crs_info": self.crs_info,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "files": [f.to_dict() for f in self.files],
        }


class JobFile(db.Model):
    __tablename__ = "job_files"

    id = db.Column(db.Integer, primary_key=True)
    job_db_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(100), nullable=True)
    file_type = db.Column(db.String(20), nullable=False, default="output")  # input/output
    size = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "label": self.label,
            "file_type": self.file_type,
            "size": self.size,
        }
