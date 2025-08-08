from datetime import datetime


def create_device_control_model(db):
    class DeviceControl(db.Model):
        __tablename__ = "device_control"
        id = db.Column(db.Integer, primary_key=True)
        device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
        command = db.Column(db.String(128), nullable=False)
        parameters = db.Column(db.JSON, nullable=True)
        status = db.Column(db.String(32), default="pending")  # pending, sent, acknowledged, failed
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        device = db.relationship("Device", backref="controls")

    return DeviceControl
