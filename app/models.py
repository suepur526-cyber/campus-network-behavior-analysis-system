from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), default="admin", nullable=False)
    display_name = db.Column(db.String(64), default="系统管理员")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CleanLog(db.Model):
    __tablename__ = "clean_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True, nullable=False)
    user_type = db.Column(db.String(32), index=True, nullable=False)
    ip_address = db.Column(db.String(45), index=True, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, nullable=False)
    target = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), index=True, nullable=False)
    application = db.Column(db.String(64), index=True, nullable=False)
    protocol = db.Column(db.String(16), index=True, nullable=False)
    port = db.Column(db.Integer, index=True, nullable=False)
    upload_bytes = db.Column(db.Integer, nullable=False, default=0)
    download_bytes = db.Column(db.Integer, nullable=False, default=0)
    total_bytes = db.Column(db.Integer, nullable=False, default=0)
    connection_count = db.Column(db.Integer, nullable=False, default=1)
    device = db.Column(db.String(80), nullable=False, default="gateway")
    source_format = db.Column(db.String(16), nullable=False, default="csv")
    is_anomaly = db.Column(db.Boolean, index=True, default=False)
    anomaly_reason = db.Column(db.String(255), default="")
    ml_score = db.Column(db.Float, default=0.0)
    cluster_label = db.Column(db.Integer, default=-1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_type": self.user_type,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(sep=" ", timespec="seconds"),
            "target": self.target,
            "category": self.category,
            "application": self.application,
            "protocol": self.protocol,
            "port": self.port,
            "upload_bytes": self.upload_bytes,
            "download_bytes": self.download_bytes,
            "total_bytes": self.total_bytes,
            "connection_count": self.connection_count,
            "device": self.device,
            "source_format": self.source_format,
            "is_anomaly": self.is_anomaly,
            "anomaly_reason": self.anomaly_reason,
            "ml_score": self.ml_score,
            "cluster_label": self.cluster_label,
        }


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey("clean_logs.id"), nullable=True, index=True)
    severity = db.Column(db.String(16), index=True, nullable=False)
    category = db.Column(db.String(64), index=True, nullable=False)
    message = db.Column(db.String(255), nullable=False)
    detected_by = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    log = db.relationship("CleanLog", backref="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "log_id": self.log_id,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "detected_by": self.detected_by,
            "created_at": self.created_at.isoformat(sep=" ", timespec="seconds"),
        }


class SystemEvent(db.Model):
    __tablename__ = "system_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(32), index=True, nullable=False)
    message = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "message": self.message,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(sep=" ", timespec="seconds"),
        }


class IngestedFile(db.Model):
    __tablename__ = "ingested_files"

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), unique=True, index=True, nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_hash = db.Column(db.String(64), index=True, nullable=False)
    row_count = db.Column(db.Integer, nullable=False, default=0)
    source_format = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "row_count": self.row_count,
            "source_format": self.source_format,
            "created_at": self.created_at.isoformat(sep=" ", timespec="seconds"),
        }
