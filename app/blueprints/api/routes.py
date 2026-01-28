from flask import request, jsonify, send_file
from app.blueprints.api import api_bp
from app.models import Ingredient, Recipe, RecipeIngredient, Product, Order
from app.extensions import db
from app.services.calculation_service import CalculationService
from app.services.report_service import ReportService
from app.utils.decorators import admin_required
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
import sqlalchemy as sa

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "API is running"})

# --- INGREDIENTS ---
@api_bp.route('/ingredients', methods=['GET'])
def get_ingredients():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    ing_query = Ingredient.query
    if query:
        ing_query = ing_query.filter(Ingredient.name.ilike(f'%{query}%'))

    pagination = ing_query.paginate(page=page, per_page=per_page)
    return jsonify({
        "ingredients": [i.to_dict() for i in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page
    })

@api_bp.route('/ingredients', methods=['POST'])
@admin_required()
def add_ingredient():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Nom manquant / الاسم مفقود"}), 400

    ing = Ingredient(
        name=data['name'],
        unit=data.get('unit', 'kg'),
        pack_size=float(data.get('pack_size', 1)),
        price_per_pack=float(data.get('price_per_pack', 0))
    )
    db.session.add(ing)
    db.session.commit()
    return jsonify(ing.to_dict()), 201

@api_bp.route('/ingredients/<int:id>', methods=['PUT'])
@admin_required()
def update_ingredient(id):
    ing = Ingredient.query.get_or_404(id)
    data = request.get_json()

    ing.name = data.get('name', ing.name)
    ing.unit = data.get('unit', ing.unit)
    ing.pack_size = float(data.get('pack_size', ing.pack_size))
    ing.price_per_pack = float(data.get('price_per_pack', ing.price_per_pack))

    db.session.commit()
    return jsonify(ing.to_dict())

@api_bp.route('/ingredients/<int:id>', methods=['DELETE'])
@admin_required()
def delete_ingredient(id):
    ing = Ingredient.query.get_or_404(id)
    db.session.delete(ing)
    db.session.commit()
    return jsonify({"message": "Ingredient deleted"}), 200

# --- RECIPES ---
@api_bp.route('/recipes', methods=['GET'])
def get_recipes():
    query = request.args.get('q', '')
    recipes_query = Recipe.query
    if query:
        recipes_query = recipes_query.filter(Recipe.name.ilike(f'%{query}%'))

    recipes = recipes_query.all()
    return jsonify({"recipes": [r.to_dict() for r in recipes]})

@api_bp.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Récupérer les détails d'une recette"""
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify({'recipe': recipe.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():
    """Créer une nouvelle recette"""
    try:
        data = request.get_json()

        # Validation des données requises
        if not data.get('name'):
            return jsonify({'error': 'Recipe name is required'}), 400
        if not data.get('selling_price'):
            return jsonify({'error': 'Selling price is required'}), 400

        # Vérifier si la recette existe déjà
        existing = Recipe.query.filter_by(name=data.get('name')).first()
        if existing:
            return jsonify({'error': 'Recipe already exists'}), 409

        # Créer la recette
        recipe = Recipe(
            name=data.get('name'),
            ingredients_json=data.get('ingredients', []),
            ingredient_count=len(data.get('ingredients', [])),
            material_cost=float(data.get('material_cost', 0)),
            labor_cost=float(data.get('labor_cost', 0)),
            packaging_cost=float(data.get('packaging_cost', 0)),
            total_cost=float(data.get('total_cost', 0)),
            selling_price=float(data.get('selling_price')),
            profit_per_unit=float(data.get('profit_per_unit', 0)),
            profit_margin=float(data.get('profit_margin', 0))
        )

        db.session.add(recipe)
        db.session.flush()

        # Support old style RecipeIngredient relationship as well
        for ing_data in data.get('ingredients', []):
            if 'ingredient_id' in ing_data:
                ri = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ing_data['ingredient_id'],
                    quantity=float(ing_data['quantity']),
                    unit=ing_data.get('unit', 'kg')
                )
                db.session.add(ri)

        db.session.commit()

        return jsonify({
            'id': recipe.id,
            'name': recipe.name,
            'message': 'Recipe saved successfully',
            'recipe': recipe.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error creating recipe: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/recipes/<int:id>', methods=['GET'])
@api_bp.route('/recipes/<int:id>', methods=['PUT'])
@admin_required()
def update_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    data = request.get_json()

    recipe.name = data.get('name', recipe.name)
    recipe.labor_cost = float(data.get('labor_cost', recipe.labor_cost or 0))
    recipe.packaging_cost = float(data.get('packaging_cost', recipe.packaging_cost or 0))
    recipe.selling_price = float(data.get('selling_price', recipe.selling_price or 0))

    if 'ingredients' in data:
        # Clear existing ingredients
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()
        for ing_data in data['ingredients']:
            ri = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ing_data['ingredient_id'],
                quantity=float(ing_data['quantity']),
                unit=ing_data.get('unit', 'kg')
            )
            db.session.add(ri)

    db.session.commit()
    return jsonify(recipe.to_dict())

@api_bp.route('/recipes/<int:id>', methods=['DELETE'])
@admin_required()
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({"message": "Recipe deleted"}), 200

# --- BACKWARD COMPATIBILITY ---
@api_bp.route('/calculate-product', methods=['POST'])
def calculate_product():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données invalides / بيانات غير صالحة", "status": "error"}), 400

    def safe_float(val, default=0.0):
        try:
            if val is None or val == '': return default
            return float(val)
        except: return default

    # Handle legacy format where ingredients might be passed directly
    loss_rate = safe_float(data.get('loss_rate'), 0.05)
    hourly_rate = safe_float(data.get('hourly_rate'), 1500)

    ingredients = data.get('ingredients', [])
    labor_hours = safe_float(data.get('labor_hours'), 0)
    packaging_cost = safe_float(data.get('packaging_cost'), 0)
    selling_price = safe_float(data.get('selling_price'), 0)
    delivery_mode = data.get('delivery_mode', 'Customer_Pays')
    delivery_cost = float(data.get('delivery_cost', 500))

    # Basic cost calculation
    res = CalculationService.calculate_product_cost(
        None,
        ingredients_data=ingredients,
        loss_rate=loss_rate,
        labor_hours=labor_hours,
        hourly_rate=hourly_rate,
        packaging_cost=packaging_cost
    )

    total_variable_cost = res['total_variable_cost']

    if delivery_mode == 'Customer_Pays':
        delivery_cost_for_us = 0
        delivery_charged_to_customer = delivery_cost
    else: # We_Pay
        delivery_cost_for_us = delivery_cost
        delivery_charged_to_customer = 0

    # Advanced logic: Seasonal pricing, Bulk discounts, TVA
    is_summer = data.get('is_summer', False)
    quantity = safe_float(data.get('quantity'), 1)

    advanced = CalculationService.apply_advanced_logic(
        base_price=selling_price,
        quantity=quantity,
        is_summer=is_summer
    )

    # We use unit_price_with_tva for final calculations
    final_selling_price = advanced['unit_price_with_tva']

    profit_per_unit = final_selling_price - total_variable_cost - delivery_cost_for_us
    profit_margin_percentage = (profit_per_unit / final_selling_price * 100) if final_selling_price > 0 else 0
    total_paid_by_customer = final_selling_price + delivery_charged_to_customer

    return jsonify({
        **res,
        **advanced,
        "delivery_cost_for_us": delivery_cost_for_us,
        "delivery_charged_to_customer": delivery_charged_to_customer,
        "profit_per_unit": round(profit_per_unit, 2),
        "profit_margin_percentage": round(profit_margin_percentage, 2),
        "total_paid_by_customer": round(total_paid_by_customer, 2),
        "status": "success"
    })

@api_bp.route('/calculate-week', methods=['POST'])
def calculate_week():
    data = request.get_json()
    products = data.get('products', [])
    fixed_costs_monthly = float(data.get('fixed_costs_monthly', 21000))
    fixed_costs_weekly = fixed_costs_monthly / 4

    total_weekly_revenue = 0
    total_weekly_contribution = 0
    total_weekly_quantity = 0

    for p in products:
        qty = float(p.get('weekly_quantity', 0))
        price = float(p.get('selling_price', 0))
        var_cost = float(p.get('variable_cost', 0))
        contrib = float(p.get('contribution_margin', price - var_cost))

        total_weekly_revenue += qty * price
        total_weekly_contribution += qty * contrib
        total_weekly_quantity += qty

    wacm = (total_weekly_contribution / total_weekly_quantity) if total_weekly_quantity > 0 else 0
    break_even_units_total = (fixed_costs_weekly / wacm) if wacm > 0 else 0

    return jsonify({
        "fixed_costs_weekly": round(fixed_costs_weekly, 2),
        "total_weekly_revenue": round(total_weekly_revenue, 2),
        "total_weekly_contribution": round(total_weekly_contribution, 2),
        "weekly_net_profit": round(total_weekly_contribution - fixed_costs_weekly, 2),
        "break_even_units_total": round(break_even_units_total, 2),
        "status": "success"
    })

# --- STATS ---
@api_bp.route('/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Calculer les indicateurs en temps réel (comparaison avec hier) pour JS"""
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        today_orders = Order.query.filter(sa.func.date(Order.order_date) == today).all()
        yesterday_orders = Order.query.filter(sa.func.date(Order.order_date) == yesterday).all()

        revenue_today = sum([o.total_price for o in today_orders])
        revenue_yesterday = sum([o.total_price for o in yesterday_orders])

        profit_today = sum([(o.recipe.profit_per_unit * o.quantity if o.recipe and o.recipe.profit_per_unit else o.total_price * 0.3) for o in today_orders])
        profit_yesterday = sum([(o.recipe.profit_per_unit * o.quantity if o.recipe and o.recipe.profit_per_unit else o.total_price * 0.3) for o in yesterday_orders])

        best_product = 'N/A'
        if today_orders:
            product_sales = {}
            for order in today_orders:
                p_name = order.recipe.name if order.recipe else 'Unknown'
                product_sales[p_name] = product_sales.get(p_name, 0) + order.quantity
            best_product = max(product_sales, key=product_sales.get)

        return jsonify({
            'revenue_today': round(revenue_today, 2),
            'revenue_yesterday': round(revenue_yesterday, 2),
            'profit_today': round(profit_today, 2),
            'profit_yesterday': round(profit_yesterday, 2),
            'orders_today': len(today_orders),
            'orders_yesterday': len(yesterday_orders),
            'best_product': best_product
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dashboard/recent-orders', methods=['GET'])
def recent_orders_api():
    """Récupérer les commandes récentes formatées pour le dashboard"""
    try:
        orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
        formatted = []
        for o in orders:
            formatted.append({
                'id': o.id,
                'date': o.order_date.strftime('%d/%m/%Y'),
                'client': o.customer_name,
                'product': o.recipe.name if o.recipe else 'Unknown',
                'total': o.total_price,
                'status': o.status
            })
        return jsonify({'orders': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dashboard/revenue-trend', methods=['GET'])
def revenue_trend_api():
    """Tendance des revenus pour Chart.js"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)
        results = db.session.query(
            sa.func.date(Order.order_date).label('day'),
            sa.func.sum(Order.total_price).label('revenue')
        ).filter(Order.order_date >= start_date).group_by('day').order_by('day').all()

        date_map = {str(r[0]): r[1] for r in results}
        labels, data = [], []
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            labels.append(day.strftime('%a'))
            data.append(float(date_map.get(day_str, 0)))
        return jsonify({'labels': labels, 'data': data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/dashboard/top-products', methods=['GET'])
def top_products_api():
    """Top produits pour Chart.js"""
    try:
        results = db.session.query(
            Recipe.name,
            sa.func.sum(Order.quantity).label('sales')
        ).join(Order, Recipe.id == Order.product_id).group_by(Recipe.name).order_by(sa.desc('sales')).limit(5).all()
        return jsonify({
            'labels': [r[0] for r in results],
            'data': [float(r[1]) for r in results]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats/daily', methods=['GET'])
def daily_stats():
    today = datetime.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())

    orders = Order.query.filter(Order.order_date >= start_of_day).all()
    revenue = sum(o.total_price for o in orders)
    total_cost = 0
    for o in orders:
        total_cost += o.total_price * 0.7

    profit = revenue - total_cost

    return jsonify({
        "revenue": round(revenue, 2),
        "profit": round(profit, 2),
        "orders_count": len(orders),
        "lang": {"fr": "Aujourd'hui", "ar": "اليوم"}
    })

@api_bp.route('/stats/weekly', methods=['GET'])
def weekly_stats():
    last_week = datetime.now() - timedelta(days=7)
    orders = Order.query.filter(Order.order_date >= last_week).all()
    revenue = sum(o.total_price for o in orders)
    return jsonify({
        "revenue": round(revenue, 2),
        "orders_count": len(orders)
    })

@api_bp.route('/stats/monthly', methods=['GET'])
def monthly_stats():
    last_month = datetime.now() - timedelta(days=30)
    orders = Order.query.filter(Order.order_date >= last_month).all()
    revenue = sum(o.total_price for o in orders)
    return jsonify({
        "revenue": round(revenue, 2),
        "orders_count": len(orders)
    })

@api_bp.route('/stats/top-products', methods=['GET'])
def top_products():
    # Query real data: Group by product and sum quantity
    results = db.session.query(
        Recipe.name,
        sa.func.sum(Order.quantity).label('sales')
    ).join(Order, Recipe.id == Order.product_id)\
     .group_by(Recipe.name)\
     .order_by(sa.desc('sales'))\
     .limit(5).all()

    if not results:
        return jsonify([
            {"name": "Gâteau Chocolat", "sales": 0},
            {"name": "Tarte Citron", "sales": 0}
        ])

    return jsonify([{"name": r[0], "sales": float(r[1])} for r in results])

@api_bp.route('/stats/trends', methods=['GET'])
def stats_trends():
    # Real trend data for the last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)

    results = db.session.query(
        sa.func.date(Order.order_date).label('day'),
        sa.func.sum(Order.total_price).label('revenue')
    ).filter(Order.order_date >= start_date)\
     .group_by('day')\
     .order_by('day').all()

    labels = []
    values = []

    # Fill in zeros for missing days
    date_map = {str(r[0]): r[1] for r in results}
    for i in range(7):
        day_date = start_date + timedelta(days=i)
        date_str = day_date.strftime('%Y-%m-%d')
        labels.append(day_date.strftime('%a'))
        values.append(float(date_map.get(date_str, 0)))

    return jsonify({
        "labels": labels,
        "values": values
    })

# --- EXPORT ---
@api_bp.route('/export/recipes/excel', methods=['GET'])
def export_recipes():
    recipes = Recipe.query.all()
    output = ReportService.generate_recipes_excel(recipes)
    return send_file(output, as_attachment=True, download_name="recipes.xlsx")

@api_bp.route('/export/recipe/<int:id>/pdf', methods=['GET'])
def export_recipe_pdf(id):
    recipe = Recipe.query.get_or_404(id)
    # Perform calculation for the report
    calc = CalculationService.calculate_product_cost(recipe)
    output = ReportService.generate_product_report(recipe.to_dict(), calc)
    return send_file(output, as_attachment=True, download_name=f"recipe_{id}.pdf")

# --- PRODUCTS ---
@api_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

# --- ORDERS ---
@api_bp.route('/orders', methods=['GET'])
def get_orders():
    """Récupérer toutes les commandes (sans JWT pour l'affichage public)"""
    try:
        orders = Order.query.order_by(Order.order_date.desc()).all()
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/orders', methods=['POST'])
@jwt_required()
def add_order():
    """Ajouter une nouvelle commande"""
    try:
        data = request.get_json()

        # Validation des données
        if not data.get('customer_name'):
            return jsonify({'error': 'Customer name is required'}), 400
        if not data.get('product_id'):
            return jsonify({'error': 'Product is required'}), 400

        quantity = int(data.get('quantity', 1))
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be a positive integer'}), 400

        # Vérifier que le produit existe
        product = Recipe.query.get(data.get('product_id'))
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Calculer le prix total si non fourni
        total_price = data.get('total_price')
        if total_price is None:
            total_price = product.selling_price * quantity

        # Parse delivery_date if provided
        delivery_date = None
        if data.get('delivery_date'):
            try:
                delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        # Créer la commande
        order = Order(
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            customer_address=data.get('customer_address'),
            product_id=data.get('product_id'),
            quantity=quantity,
            total_price=float(total_price),
            delivery_mode=data.get('delivery_mode', 'Customer Pays'),
            delivery_date=delivery_date,
            notes=data.get('notes'),
            status='Pending'
        )

        db.session.add(order)
        db.session.commit()

        return jsonify({
            'id': order.id,
            'message': 'Order added successfully',
            'order': order.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error adding order: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Récupérer les détails d'une commande spécifique"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        unit_price = order.total_price / order.quantity if order.quantity > 0 else 0

        return jsonify({
            'id': order.id,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone or 'N/A',
            'customer_address': order.customer_address or 'N/A',
            'product_name': order.recipe.name if order.recipe else 'Unknown',
            'product_id': order.product_id,
            'quantity': order.quantity,
            'unit_price': unit_price,
            'total_price': order.total_price,
            'delivery_mode': order.delivery_mode,
            'delivery_date': order.delivery_date.strftime('%d/%m/%Y') if order.delivery_date else 'N/A',
            'status': order.status,
            'notes': order.notes or 'Aucune',
            'order_date': order.order_date.strftime('%d/%m/%Y %H:%M')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/orders/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    """Mettre à jour une commande existante"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        data = request.get_json()

        # Mettre à jour les champs autorisés
        if 'status' in data:
            order.status = data['status']
        if 'customer_phone' in data:
            order.customer_phone = data['customer_phone']
        if 'customer_address' in data:
            order.customer_address = data['customer_address']
        if 'delivery_date' in data:
            try:
                order.delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
            except:
                pass
        if 'notes' in data:
            order.notes = data['notes']
        if 'quantity' in data:
            order.quantity = int(data['quantity'])
        if 'total_price' in data:
            order.total_price = float(data['total_price'])

        db.session.commit()

        return jsonify({
            'message': 'Order updated successfully',
            'order': order.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error updating order: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    """Supprimer une commande"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        db.session.delete(order)
        db.session.commit()

        return jsonify({'message': 'Order deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting order: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@api_bp.route('/orders/<int:order_id>/print', methods=['GET'])
def print_order(order_id):
    """Retourner un HTML pour l'impression du bon de commande"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return "Commande non trouvée", 404

        unit_price = order.total_price / order.quantity if order.quantity > 0 else 0

        html = f"""
        <html>
        <head>
            <title>Bon de Commande #{order.id}</title>
            <style>
                body {{ font-family: sans-serif; padding: 40px; line-height: 1.6; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .details {{ margin-top: 30px; }}
                .table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .table th {{ background-color: #f2 f2 f2; }}
                .footer {{ margin-top: 50px; text-align: center; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎂 GESTION PÂTISSERIE ALGER</h1>
                <p>BON DE COMMANDE #{order.id}</p>
            </div>
            <div class="details">
                <p><strong>Date:</strong> {order.order_date.strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>Client:</strong> {order.customer_name}</p>
                <p><strong>Téléphone:</strong> {order.customer_phone or 'N/A'}</p>
                <p><strong>Adresse:</strong> {order.customer_address or 'N/A'}</p>
            </div>
            <table class="table">
                <thead>
                    <tr>
                        <th>Produit</th>
                        <th>Quantité</th>
                        <th>Prix Unitaire</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{order.recipe.name if order.recipe else 'Inconnu'}</td>
                        <td>{order.quantity}</td>
                        <td>{unit_price:.2f} DA</td>
                        <td>{order.total_price:.2f} DA</td>
                    </tr>
                </tbody>
            </table>
            <div class="details">
                <p><strong>Mode Livraison:</strong> {order.delivery_mode}</p>
                <p><strong>Date Livraison:</strong> {order.delivery_date.strftime('%d/%m/%Y') if order.delivery_date else 'N/A'}</p>
                <p><strong>Notes:</strong> {order.notes or 'Aucune'}</p>
            </div>
            <div class="footer">
                <p>Merci pour votre confiance ! / شكرا لثقتكم</p>
            </div>
        </body>
        </html>
        """
        return html, 200
    except Exception as e:
        return str(e), 500
