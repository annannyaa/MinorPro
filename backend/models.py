from config import db

class Dustbin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(80), unique=False, nullable=False)
    latitude = db.Column(db.String(80), unique=False, nullable=False)
    longitude = db.Column(db.String(80), unique=False, nullable=False)
    capacity = db.Column(db.String(5), unique=False, nullable=False)  # Format: "HH:MM"

    def to_json(self):
        return {
            "id": self.id,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacity": self.capacity
        }
