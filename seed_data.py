from app import create_app
from app.extensions import db
from app.models import Ingredient, Recipe, RecipeIngredient, User, Product, Order

def seed():
    app = create_app()
    with app.app_context():
        # Create Admin User
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        # Ingredients
        ingredients_data = [
            {"name": "Farine", "unit": "kg", "pack_size": 1, "price_per_pack": 100},
            {"name": "Sucre", "unit": "kg", "pack_size": 1, "price_per_pack": 100},
            {"name": "Œufs", "unit": "pcs", "pack_size": 12, "price_per_pack": 240},
            {"name": "Orange", "unit": "kg", "pack_size": 1, "price_per_pack": 150},
            {"name": "Citron", "unit": "kg", "pack_size": 1, "price_per_pack": 200},
            {"name": "Fraise", "unit": "kg", "pack_size": 1, "price_per_pack": 600},
            {"name": "Eau", "unit": "L", "pack_size": 1, "price_per_pack": 0},
            {"name": "Fruits Mixtes", "unit": "kg", "pack_size": 1, "price_per_pack": 500}
        ]

        ing_objs = {}
        for data in ingredients_data:
            ing = Ingredient.query.filter_by(name=data['name']).first()
            if not ing:
                ing = Ingredient(**data)
                db.session.add(ing)
            ing_objs[data['name']] = ing

        db.session.commit()

        # Recipes
        recipes_data = [
            {
                "name": "Gâteau Chocolat",
                "labor_hours": 1.5,
                "packaging_cost": 100,
                "selling_price": 3500,
                "ingredients": [
                    {"name": "Farine", "quantity": 0.5},
                    {"name": "Sucre", "quantity": 0.2},
                    {"name": "Œufs", "quantity": 4}
                ]
            },
            {
                "name": "Jus d'Orange",
                "labor_hours": 0.3,
                "packaging_cost": 50,
                "selling_price": 800,
                "ingredients": [
                    {"name": "Orange", "quantity": 1.0},
                    {"name": "Sucre", "quantity": 0.1},
                    {"name": "Eau", "quantity": 0.5}
                ]
            },
            {
                "name": "Jus de Citron",
                "labor_hours": 0.3,
                "packaging_cost": 50,
                "selling_price": 900,
                "ingredients": [
                    {"name": "Citron", "quantity": 0.5},
                    {"name": "Sucre", "quantity": 0.15},
                    {"name": "Eau", "quantity": 0.5}
                ]
            }
        ]

        for r_data in recipes_data:
            recipe = Recipe.query.filter_by(name=r_data['name']).first()
            if not recipe:
                recipe = Recipe(
                    name=r_data['name'],
                    labor_hours=r_data['labor_hours'],
                    packaging_cost=r_data['packaging_cost'],
                    selling_price=r_data['selling_price']
                )
                db.session.add(recipe)
                db.session.flush()

                for ing_info in r_data['ingredients']:
                    ri = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ing_objs[ing_info['name']].id,
                        quantity=ing_info['quantity'],
                        unit=ing_objs[ing_info['name']].unit
                    )
                    db.session.add(ri)

        db.session.commit()

        # Seed Products and Orders
        from datetime import datetime, timedelta
        recipes = Recipe.query.all()
        for r in recipes:
            p = Product.query.filter_by(recipe_id=r.id).first()
            if not p:
                p = Product(recipe_id=r.id, quantity_produced=100)
                db.session.add(p)
                db.session.flush()

            # Add some orders for this product
            if not Order.query.filter_by(product_id=p.id).first():
                for i in range(5):
                    o = Order(
                        product_id=p.id,
                        quantity=2,
                        total_price=r.selling_price * 2,
                        customer_name=f"Client {i}",
                        created_at=datetime.utcnow() - timedelta(days=i)
                    )
                    db.session.add(o)

        db.session.commit()
        print("Database seeded with orders!")

if __name__ == '__main__':
    seed()
