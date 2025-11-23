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
    devices = db.relationship("Device", backref="owner", lazy="dynamic", cascade="all, delete-orphan")

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

    def set_password(self, password):
        """Hash and set user password"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


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
    status = db.Column(db.String(20), nullable=False, default="inactive")  # active, inactive, maintenance
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
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))

    # Relationships
    # Removed: auth_records, configurations (tables no longer exist)

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

    def set_status(self, status):
        """Set device status"""
        self.status = status
        db.session.commit()

    def get_status(self):
        """Get device status from database"""
        return self.status

    def is_authenticated(self, api_key):
        """Check if the provided API key matches the device's API key"""
        return self.api_key == api_key and self.status == "active"

    @staticmethod
    def authenticate_by_api_key(api_key):
        """Authenticate device by API key"""
        return Device.query.filter_by(api_key=api_key, status="active").first()

# Removed DeviceAuth and DeviceConfiguration models - tables no longer exist


# Chart models removed - no longer needed


class DeviceGroup(db.Model):
    """Device group for organizing devices"""
    
    __tablename__ = "device_groups"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    color = db.Column(db.String(7))  # Hex color
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    members = db.relationship("DeviceGroupMember", backref="group", lazy="dynamic", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        db.Index("idx_user_groups", "user_id"),
        db.Index("idx_group_name", "name"),
    )
    
    def __repr__(self):
        return f"<DeviceGroup {self.name}>"
    
    def to_dict(self, include_devices=False):
        """Convert group to dictionary"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'device_count': self.members.count()
        }
        
        if include_devices:
            result['devices'] = [member.device.to_dict() for member in self.members]
        
        return result


class DeviceGroupMember(db.Model):
    """Many-to-many relationship between groups and devices"""
    
    __tablename__ = "device_group_members"
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("device_groups.id", ondelete="CASCADE"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    added_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    device = db.relationship("Device", backref="group_memberships")
    
    # Constraints and Indexes
    __table_args__ = (
        db.UniqueConstraint("group_id", "device_id", name="unique_group_device"),
        db.Index("idx_group_members", "group_id"),
        db.Index("idx_device_groups", "device_id"),
    )
    
    def __repr__(self):
        return f"<DeviceGroupMember group={self.group_id} device={self.device_id}>"
    
    def to_dict(self):
        """Convert membership to dictionary"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'device_id': self.device_id,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }



