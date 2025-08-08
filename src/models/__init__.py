from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import secrets
import string
import uuid

db = SQLAlchemy()


def generate_api_key(length=32):
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_user_id():
    """Generate a unique user ID"""
    return uuid.uuid4().hex


class User(db.Model):
    """User model for storing user account information"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), unique=True, nullable=False, default=generate_user_id)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login = db.Column(db.DateTime(timezone=True))

    # Relationships
    devices = db.relationship("Device", backref="owner", lazy="dynamic")

    # Indexes
    __table_args__ = (
        db.Index("idx_email", "email"),
        db.Index("idx_username", "username"),
        db.Index("idx_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    # Authentication methods can be added here


class Device(db.Model):
    """Device model for storing IoT device information"""

    __tablename__ = "devices"

    # Table arguments including indexes
    __table_args__ = (db.Index("idx_devices_user_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    device_type = db.Column(db.String(50), nullable=False, default="sensor")
    api_key = db.Column(db.String(64), unique=True, nullable=False, default=generate_api_key)
    status = db.Column(db.String(20), nullable=False, default="active")  # active, inactive, maintenance
    location = db.Column(db.String(200))
    firmware_version = db.Column(db.String(20))
    hardware_version = db.Column(db.String(20))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_seen = db.Column(db.DateTime(timezone=True))

    # Foreign Key Relationship to User
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Relationships
    auth_records = db.relationship("DeviceAuth", backref="device", lazy="dynamic", cascade="all, delete-orphan")
    configurations = db.relationship(
        "DeviceConfiguration",
        backref="device",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Device {self.name}>"

    def to_dict(self):
        """Convert device to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "device_type": self.device_type,
            "status": self.status,
            "location": self.location,
            "firmware_version": self.firmware_version,
            "hardware_version": self.hardware_version,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }

    def update_last_seen(self):
        """Update the last seen timestamp"""
        self.last_seen = datetime.now(timezone.utc)
        db.session.commit()

        # Also update Redis cache if available
        from flask import current_app

        if hasattr(current_app, "device_status_cache") and current_app.device_status_cache:
            current_app.device_status_cache.update_device_last_seen(self.id)
            current_app.device_status_cache.set_device_status(self.id, "online")

    def set_status(self, status):
        """Set device status and update Redis cache"""
        self.status = status
        db.session.commit()

        # Also update Redis cache if available
        from flask import current_app

        if hasattr(current_app, "device_status_cache") and current_app.device_status_cache:
            current_app.device_status_cache.set_device_status(self.id, status)

    def get_status(self):
        """Get device status with Redis cache priority"""
        from flask import current_app

        # Try to get from Redis cache first
        if hasattr(current_app, "device_status_cache") and current_app.device_status_cache:
            redis_status = current_app.device_status_cache.get_device_status(self.id)
            if redis_status:
                return redis_status

        # Fall back to database status
        return self.status

    def is_authenticated(self, api_key):
        """Check if the provided API key matches the device's API key"""
        return self.api_key == api_key and self.status == "active"

    @staticmethod
    def authenticate_by_api_key(api_key):
        """Authenticate device by API key"""
        return Device.query.filter_by(api_key=api_key, status="active").first()

    @staticmethod
    def authenticate_by_mqtt_credentials(username, password):
        """Authenticate device by MQTT username/password (username=device_id, password=api_key)"""
        try:
            device_id = int(username)
            device = Device.query.filter_by(id=device_id, status="active").first()
            if device and device.api_key == password:
                return device
        except (ValueError, TypeError):
            pass
        return None


class DeviceAuth(db.Model):
    """Device authentication model for API key management"""

    __tablename__ = "device_auth"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    api_key_hash = db.Column(db.String(128), nullable=False)  # Hashed version of API key
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime(timezone=True))  # Optional expiration
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used = db.Column(db.DateTime(timezone=True))
    usage_count = db.Column(db.Integer, default=0)

    # Indexes
    __table_args__ = (
        db.Index("idx_api_key_hash", "api_key_hash"),
        db.Index("idx_device_auth", "device_id", "is_active"),
    )

    def __repr__(self):
        return f"<DeviceAuth device_id={self.device_id} active={self.is_active}>"

    def increment_usage(self):
        """Increment usage counter and update last used timestamp"""
        self.usage_count += 1
        self.last_used = datetime.now(timezone.utc)
        db.session.commit()


class DeviceConfiguration(db.Model):
    """Device configuration model for storing device-specific settings"""

    __tablename__ = "device_configurations"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    config_key = db.Column(db.String(100), nullable=False)
    config_value = db.Column(db.Text)
    data_type = db.Column(db.String(20), default="string")  # string, integer, float, boolean, json
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Unique constraint to prevent duplicate config keys per device
    __table_args__ = (
        db.UniqueConstraint("device_id", "config_key", name="uq_device_config"),
        db.Index("idx_device_config", "device_id", "is_active"),
    )

    def __repr__(self):
        return f"<DeviceConfiguration device_id={self.device_id} key={self.config_key}>"


class Chart(db.Model):
    """Chart model for storing user-specific chart configurations"""

    __tablename__ = "charts"

    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    time_range = db.Column(db.String(20), default="1h")
    refresh_interval = db.Column(db.Integer, default=30)
    aggregation = db.Column(db.String(20), default="none")
    group_by = db.Column(db.String(50), default="device")
    appearance_config = db.Column(db.JSON)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    devices = db.relationship("ChartDevice", backref="chart", lazy="dynamic", cascade="all, delete-orphan")
    measurements = db.relationship(
        "ChartMeasurement",
        backref="chart",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index("idx_user_charts", "user_id"),
        db.Index("idx_chart_type", "type"),
        db.Index("idx_created_at", "created_at"),
    )


class ChartDevice(db.Model):
    """ChartDevice model for associating devices with charts"""

    __tablename__ = "chart_devices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chart_id = db.Column(db.String(255), db.ForeignKey("charts.id", ondelete="CASCADE"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("chart_id", "device_id", name="unique_chart_device"),
        db.Index("idx_chart_devices", "chart_id"),
        db.Index("idx_device_charts", "device_id"),
    )


class ChartMeasurement(db.Model):
    """ChartMeasurement model for storing measurement configurations in charts"""

    __tablename__ = "chart_measurements"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chart_id = db.Column(db.String(255), db.ForeignKey("charts.id", ondelete="CASCADE"), nullable=False)
    measurement_name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    color = db.Column(db.String(7))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint("chart_id", "measurement_name", name="unique_chart_measurement"),
        db.Index("idx_chart_measurements", "chart_id"),
        db.Index("idx_measurement_name", "measurement_name"),
    )


# Create the DeviceControl model after all other models are defined
from src.models.device_control import create_device_control_model  # noqa: E402

DeviceControl = create_device_control_model(db)
