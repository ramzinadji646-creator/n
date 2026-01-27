from app.extensions import db
from datetime import datetime

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    pack_size = db.Column(db.Float, nullable=False)
    price_per_pack = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "unit": self.unit,
            "pack_size": self.pack_size,
            "price_per_pack": self.price_per_pack,
            "created_at": self.created_at.isoformat()
        }
