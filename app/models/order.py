from app.extensions import db
from datetime import datetime

from app.models.recipe import Recipe

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_address = db.Column(db.String(255), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False)
    delivery_mode = db.Column(db.String(50), nullable=False, default='Customer Pays')
    delivery_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Pending', nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # Relation avec Recipe
    recipe = db.relationship('Recipe', backref='orders')

    def to_dict(self):
        try:
            return {
                'id': self.id,
                'order_date': self.order_date.strftime('%d/%m/%Y'),
                'customer_name': self.customer_name,
                'customer_phone': self.customer_phone or 'N/A',
                'customer_address': self.customer_address or 'N/A',
                'product': self.recipe.name if self.recipe else 'Unknown Product',
                'product_id': self.product_id,
                'quantity': self.quantity,
                'total_price': self.total_price,
                'delivery_mode': self.delivery_mode,
                'delivery_date': self.delivery_date.strftime('%d/%m/%Y') if self.delivery_date else 'N/A',
                'status': self.status,
                'notes': self.notes or ''
            }
        except Exception as e:
            print(f"Error converting order to dict: {e}")
            return {}
