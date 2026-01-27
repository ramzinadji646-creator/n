from app.extensions import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    quantity_produced = db.Column(db.Float, nullable=False)
    production_date = db.Column(db.DateTime, default=datetime.utcnow)
    actual_cost = db.Column(db.Float)
    actual_profit = db.Column(db.Float)

    recipe = db.relationship('Recipe', backref='products')

    def to_dict(self):
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "recipe_name": self.recipe.name if self.recipe else None,
            "quantity_produced": self.quantity_produced,
            "production_date": self.production_date.isoformat(),
            "actual_cost": self.actual_cost,
            "actual_profit": self.actual_profit
        }
