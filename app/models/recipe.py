from app.extensions import db
from datetime import datetime

class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    ingredients_json = db.Column(db.JSON, nullable=True) # Renamed to avoid conflict with relationship
    ingredient_count = db.Column(db.Integer, nullable=True)
    material_cost = db.Column(db.Float, nullable=True)
    labor_cost = db.Column(db.Float, nullable=True)
    packaging_cost = db.Column(db.Float, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    selling_price = db.Column(db.Float, nullable=False)
    profit_per_unit = db.Column(db.Float, nullable=True)
    profit_margin = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ingredient_count': self.ingredient_count or 0,
            'selling_price': self.selling_price,
            'profit_margin': self.profit_margin or 0,
            'ingredients': [ri.to_dict() for ri in self.ingredients]
        }

class RecipeIngredient(db.Model):
    __tablename__ = 'recipe_ingredients'
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), primary_key=True)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)

    ingredient = db.relationship('Ingredient')

    def to_dict(self):
        return {
            "ingredient_id": self.ingredient_id,
            "name": self.ingredient.name if self.ingredient else None,
            "quantity": self.quantity,
            "unit": self.unit,
            "price_per_pack": self.ingredient.price_per_pack if self.ingredient else None,
            "pack_size": self.ingredient.pack_size if self.ingredient else None
        }
