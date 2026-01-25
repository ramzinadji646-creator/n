import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

RECIPES_FILE = 'data/recipes.json'

def load_data():
    """Loads recipes and ingredients from the JSON file."""
    try:
        with open(RECIPES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"ingredients": [], "recipes": [], "parameters": {}}

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "API is running / API est en cours d'exécution / API قيد التشغيل"})

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Returns predefined recipes and ingredients."""
    data = load_data()
    return jsonify(data)

@app.route('/api/calculate-product', methods=['POST'])
def calculate_product():
    """Calculates cost and profit for a single product."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Erreur: Données manquantes / خطأ: بيانات مفقودة"}), 400

    try:
        product_name = data.get('product_name')
        ingredients = data.get('ingredients', [])
        packaging_cost = float(data.get('packaging_cost', 0))
        labor_hours = float(data.get('labor_hours', 0))
        hourly_rate = float(data.get('hourly_rate', 1500))
        loss_rate = float(data.get('loss_rate', 0.05))
        selling_price = float(data.get('selling_price', 0))
        delivery_mode = data.get('delivery_mode', 'Customer_Pays')
        delivery_cost = float(data.get('delivery_cost', 500))

        if any(v < 0 for v in [packaging_cost, labor_hours, hourly_rate, loss_rate, selling_price, delivery_cost]):
             return jsonify({"error": "Erreur: Les valeurs négatives ne sont pas autorisées / خطأ: القيم السالبة غير مسموح بها"}), 400

        total_ingredient_cost_raw = 0
        for ing in ingredients:
            qty = float(ing.get('quantity', 0))
            price_pack = float(ing.get('price_per_pack', 0))
            pack_size = float(ing.get('pack_size', 1))
            if qty < 0 or price_pack < 0 or pack_size <= 0:
                return jsonify({"error": "Erreur: Données d'ingrédients invalides / خطأ: بيانات المكونات غير صالحة"}), 400

            unit_cost = price_pack / pack_size
            total_ingredient_cost_raw += qty * unit_cost

        ingredient_cost_with_loss = total_ingredient_cost_raw * (1 + loss_rate)
        labor_cost = labor_hours * hourly_rate
        total_variable_cost = ingredient_cost_with_loss + packaging_cost + labor_cost

        if delivery_mode == 'Customer_Pays':
            delivery_cost_for_us = 0
            delivery_charged_to_customer = delivery_cost
        else: # We_Pay
            delivery_cost_for_us = delivery_cost
            delivery_charged_to_customer = 0

        profit_per_unit = selling_price - total_variable_cost - delivery_cost_for_us
        profit_margin_percentage = (profit_per_unit / selling_price * 100) if selling_price > 0 else 0
        total_paid_by_customer = selling_price + delivery_charged_to_customer

        return jsonify({
            "ingredient_cost_raw": round(total_ingredient_cost_raw, 2),
            "ingredient_cost_with_loss": round(ingredient_cost_with_loss, 2),
            "labor_cost": round(labor_cost, 2),
            "packaging_cost": round(packaging_cost, 2),
            "delivery_cost_for_us": round(delivery_cost_for_us, 2),
            "delivery_charged_to_customer": round(delivery_charged_to_customer, 2),
            "total_variable_cost": round(total_variable_cost, 2),
            "selling_price": round(selling_price, 2),
            "profit_per_unit": round(profit_per_unit, 2),
            "profit_margin_percentage": round(profit_margin_percentage, 2),
            "status": "success",
            "total_paid_by_customer": round(total_paid_by_customer, 2)
        })

    except (ValueError, TypeError):
        return jsonify({"error": "Erreur: Format de données invalide / خطأ: تنسيق بيانات غير صالح"}), 400

@app.route('/api/calculate-week', methods=['POST'])
def calculate_week():
    """Calculates weekly revenue and break-even analysis."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Erreur: Données manquantes / خطأ: بيانات مفقودة"}), 400

    try:
        products = data.get('products', [])
        fixed_costs_monthly = float(data.get('fixed_costs_monthly', 21000))

        if fixed_costs_monthly < 0:
            return jsonify({"error": "Erreur: Charges fixes négatives / خطأ: التكاليف الثابتة سالبة"}), 400

        fixed_costs_weekly = fixed_costs_monthly / 4

        total_weekly_revenue = 0
        total_weekly_variable_costs = 0
        total_weekly_contribution = 0
        total_weekly_quantity = 0
        weighted_contribution_sum = 0

        for p in products:
            qty = float(p.get('weekly_quantity', 0))
            price = float(p.get('selling_price', 0))
            var_cost = float(p.get('variable_cost', 0))
            contrib_margin = float(p.get('contribution_margin', price - var_cost))

            if qty < 0 or price < 0 or var_cost < 0:
                 return jsonify({"error": "Erreur: Données de produit invalides / خطأ: بيانات المنتج غير صالحة"}), 400

            total_weekly_revenue += qty * price
            total_weekly_variable_costs += qty * var_cost
            total_weekly_contribution += qty * contrib_margin
            total_weekly_quantity += qty
            weighted_contribution_sum += qty * contrib_margin

        if total_weekly_quantity == 0:
             return jsonify({"error": "Erreur: Quantité totale hebdomadaire nulle / خطأ: إجمالي الكمية الأسبوعية صفر"}), 400

        weekly_profit_before_fixed = total_weekly_contribution
        weekly_net_profit = weekly_profit_before_fixed - fixed_costs_weekly

        wacm = weighted_contribution_sum / total_weekly_quantity
        break_even_units_total = (fixed_costs_weekly / wacm) if wacm > 0 else 0

        avg_selling_price = total_weekly_revenue / total_weekly_quantity
        break_even_revenue = break_even_units_total * avg_selling_price

        break_even_per_product = []
        for p in products:
            qty = float(p.get('weekly_quantity', 0))
            proportion = qty / total_weekly_quantity
            break_even_per_product.append({
                "product_name": p.get('name'),
                "units": round(proportion * break_even_units_total, 2)
            })

        return jsonify({
            "fixed_costs_weekly": round(fixed_costs_weekly, 2),
            "total_weekly_revenue": round(total_weekly_revenue, 2),
            "total_weekly_variable_costs": round(total_weekly_variable_costs, 2),
            "total_weekly_contribution": round(total_weekly_contribution, 2),
            "weekly_profit_before_fixed": round(weekly_profit_before_fixed, 2),
            "weekly_net_profit": round(weekly_net_profit, 2),
            "break_even_units_total": round(break_even_units_total, 2),
            "break_even_revenue": round(break_even_revenue, 2),
            "break_even_per_product": break_even_per_product,
            "status": "success"
        })

    except (ValueError, TypeError, ZeroDivisionError):
        return jsonify({"error": "Erreur: Données invalides pour le calcul hebdomadaire / خطأ: بيانات غير صالحة للحساب الأسبوعي"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
