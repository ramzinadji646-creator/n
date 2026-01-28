from app.extensions import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer_name = db.Column(db.String(100))
    delivery_mode = db.Column(db.String(50)) # Customer_Pays, We_Pay, Free
    status = db.Column(db.String(20), default='Pending') # Pending, In Progress, Completed, Cancelled

    product = db.relationship('Product', backref='orders')

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.recipe.name if self.product and self.product.recipe else f"Produit #{self.product_id}",
            "quantity": self.quantity,
            "total_price": self.total_price,
            "created_at": self.created_at.isoformat(),
            "customer_name": self.customer_name,
            "delivery_mode": self.delivery_mode,
            "status": self.status
        }
