import pytest
from app.services.calculation_service import CalculationService

def test_calculate_product_cost_basic():
    # Mocking recipe structure
    class MockIngredient:
        def __init__(self, price, size):
            self.price_per_pack = price
            self.pack_size = size

    class MockRecipeIngredient:
        def __init__(self, quantity, ingredient):
            self.quantity = quantity
            self.ingredient = ingredient

    class MockRecipe:
        def __init__(self, labor, pkg):
            self.labor_hours = labor
            self.packaging_cost = pkg
            self.ingredients = []

    ing = MockIngredient(100, 1)
    ri = MockRecipeIngredient(0.5, ing)
    recipe = MockRecipe(1.5, 100)
    recipe.ingredients = [ri]

    res = CalculationService.calculate_product_cost(recipe, hourly_rate=1500, loss_rate=0.05)

    # 0.5 * 100 * 1.05 = 52.5
    # 1.5 * 1500 = 2250
    # Pkg = 100
    # Total = 52.5 + 2250 + 100 = 2402.5
    assert res['total_variable_cost'] == 2402.5

def test_apply_advanced_logic():
    # Summer pricing +10%
    res = CalculationService.apply_advanced_logic(1000, 1, is_summer=True, tva_rate=0.19)
    # 1000 * 1.1 = 1100
    assert res['unit_price_net'] == 1100.0
    # 1100 * 1.19 = 1309
    assert res['unit_price_with_tva'] == 1309.0

    # Bulk discount 10%
    res = CalculationService.apply_advanced_logic(1000, 50, is_summer=False, tva_rate=0)
    # 1000 * 0.9 = 900
    assert res['unit_price_net'] == 900.0
    assert res['total_net'] == 45000.0
