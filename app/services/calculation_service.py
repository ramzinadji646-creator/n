class CalculationService:
    @staticmethod
    def calculate_product_cost(recipe, ingredients_data=None, loss_rate=0.05, labor_hours=None, hourly_rate=1500, packaging_cost=None):
        """
        Calculates costs for a recipe.
        If ingredients_data is provided, it uses that (for temporary calculations).
        Otherwise, it uses the ingredients linked to the recipe in the DB.
        """
        total_ingredient_cost_raw = 0

        def safe_float(val, default=0.0):
            try:
                if val is None or val == '':
                    return default
                return float(val)
            except (ValueError, TypeError):
                return default

        if ingredients_data is not None:
            for ing in ingredients_data:
                qty = safe_float(ing.get('quantity', 0))
                price_pack = safe_float(ing.get('price_per_pack', 0))
                pack_size = safe_float(ing.get('pack_size', 1), default=1.0)
                if pack_size == 0: pack_size = 1.0
                total_ingredient_cost_raw += qty * (price_pack / pack_size)
        elif recipe is not None:
            for ri in recipe.ingredients:
                total_ingredient_cost_raw += ri.quantity * (ri.ingredient.price_per_pack / ri.ingredient.pack_size)

        ingredient_cost_with_loss = total_ingredient_cost_raw * (1 + loss_rate)

        labor_cost = 0
        if labor_hours is not None:
            labor_cost = safe_float(labor_hours) * safe_float(hourly_rate, default=1500.0)
        elif recipe is not None:
            # Check for new labor_cost field first
            if hasattr(recipe, 'labor_cost') and recipe.labor_cost is not None:
                labor_cost = recipe.labor_cost
            elif hasattr(recipe, 'labor_hours') and recipe.labor_hours is not None:
                labor_cost = recipe.labor_hours * safe_float(hourly_rate, default=1500.0)

        pkg = 0
        if packaging_cost is not None:
            pkg = safe_float(packaging_cost)
        elif recipe is not None:
            pkg = recipe.packaging_cost

        total_variable_cost = ingredient_cost_with_loss + pkg + labor_cost

        return {
            "ingredient_cost_raw": round(total_ingredient_cost_raw, 2),
            "ingredient_cost_with_loss": round(ingredient_cost_with_loss, 2),
            "labor_cost": round(labor_cost, 2),
            "packaging_cost": round(pkg, 2),
            "total_variable_cost": round(total_variable_cost, 2)
        }

    @staticmethod
    def apply_advanced_logic(base_price, quantity, is_summer=False, tva_rate=0.19):
        """
        Applies seasonal pricing, bulk discounts, and TVA.
        """
        price = base_price

        # Seasonal pricing (+10% in summer)
        if is_summer:
            price *= 1.10

        # Bulk discounts
        discount = 0
        if quantity >= 50:
            discount = 0.10
        elif quantity >= 10:
            discount = 0.05

        price *= (1 - discount)

        # TVA
        price_with_tva = price * (1 + tva_rate)

        return {
            "unit_price_net": round(price, 2),
            "unit_price_with_tva": round(price_with_tva, 2),
            "total_net": round(price * quantity, 2),
            "total_with_tva": round(price_with_tva * quantity, 2),
            "discount_applied": discount
        }
