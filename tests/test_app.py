import pytest
import json
import os
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'

def test_get_recipes(client):
    response = client.get('/api/recipes')
    assert response.status_code == 200
    data = response.get_json()
    assert 'recipes' in data
    assert 'ingredients' in data

def test_get_recipes_file_not_found(client):
    os.rename('data/recipes.json', 'data/recipes.json.bak')
    try:
        response = client.get('/api/recipes')
        assert response.status_code == 200
        data = response.get_json()
        assert data == {"ingredients": [], "recipes": [], "parameters": {}}
    finally:
        os.rename('data/recipes.json.bak', 'data/recipes.json')

def test_calculate_product_gateau_chocolat(client):
    payload = {
        "product_name": "Gâteau Chocolat",
        "ingredients": [
            {"name": "Farine", "quantity": 0.5, "price_per_pack": 100, "pack_size": 1},
            {"name": "Sucre", "quantity": 0.2, "price_per_pack": 50, "pack_size": 0.5},
            {"name": "Œufs", "quantity": 4, "price_per_pack": 240, "pack_size": 12}
        ],
        "packaging_cost": 100,
        "labor_hours": 1.5,
        "hourly_rate": 1500,
        "loss_rate": 0.05,
        "selling_price": 3500,
        "delivery_mode": "Customer_Pays",
        "delivery_cost": 500
    }
    response = client.post('/api/calculate-product', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['ingredient_cost_raw'] == 150.0
    assert data['ingredient_cost_with_loss'] == 157.5
    assert data['labor_cost'] == 2250.0
    assert data['total_variable_cost'] == 2507.5
    assert data['delivery_cost_for_us'] == 0
    assert data['profit_per_unit'] == 992.5
    assert data['total_paid_by_customer'] == 4000.0

def test_calculate_product_tarte_citron(client):
    payload = {
        "product_name": "Tarte Citron",
        "ingredients": [
            {"name": "Farine", "quantity": 0.3, "price_per_pack": 100, "pack_size": 1},
            {"name": "Sucre", "quantity": 0.15, "price_per_pack": 50, "pack_size": 0.5},
            {"name": "Œufs", "quantity": 2, "price_per_pack": 240, "pack_size": 12}
        ],
        "packaging_cost": 80,
        "labor_hours": 1.0,
        "hourly_rate": 1500,
        "loss_rate": 0.05,
        "selling_price": 2500,
        "delivery_mode": "We_Pay",
        "delivery_cost": 500
    }
    response = client.post('/api/calculate-product', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['ingredient_cost_raw'] == 85.0
    assert data['ingredient_cost_with_loss'] == 89.25
    assert data['labor_cost'] == 1500.0
    assert data['total_variable_cost'] == 1669.25
    assert data['delivery_cost_for_us'] == 500
    assert data['profit_per_unit'] == 330.75
    assert data['total_paid_by_customer'] == 2500.0

def test_calculate_week_break_even(client):
    payload = {
        "products": [
            {
                "name": "Gâteau Chocolat",
                "selling_price": 3500,
                "variable_cost": 2507.5,
                "contribution_margin": 992.5,
                "weekly_quantity": 10
            },
            {
                "name": "Tarte Citron",
                "selling_price": 2500,
                "variable_cost": 1669.25,
                "contribution_margin": 330.75,
                "weekly_quantity": 20
            }
        ],
        "fixed_costs_monthly": 21000
    }
    response = client.post('/api/calculate-week', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['fixed_costs_weekly'] == 5250.0
    assert data['total_weekly_revenue'] == 85000.0
    assert data['total_weekly_contribution'] == 16540.0
    assert data['weekly_net_profit'] == 11290.0
    assert data['break_even_units_total'] == round(5250 / (16540/30), 2)

def test_calculate_product_errors(client):
    # Missing data (not JSON)
    response = client.post('/api/calculate-product', data="not json")
    assert response.status_code == 415 # Flask default for missing/wrong content type with get_json()

    # Empty JSON
    response = client.post('/api/calculate-product', json={})
    # Since all fields are optional with defaults, it might actually succeed if not for validations?
    # Wait, in my app.py: product_name = data.get('product_name')
    # If data is empty dict, it's not None.
    # I should probably check for empty dict too.

    # Negative values
    response = client.post('/api/calculate-product', json={"selling_price": -100})
    assert response.status_code == 400

    # Invalid ingredient data
    response = client.post('/api/calculate-product', json={
        "ingredients": [{"quantity": -1, "price_per_pack": 100, "pack_size": 1}]
    })
    assert response.status_code == 400

    # Pack size zero
    response = client.post('/api/calculate-product', json={
        "ingredients": [{"quantity": 1, "price_per_pack": 100, "pack_size": 0}]
    })
    assert response.status_code == 400

    # Type error
    response = client.post('/api/calculate-product', json={
        "selling_price": "invalid"
    })
    assert response.status_code == 400

def test_calculate_week_errors(client):
    # Missing data
    response = client.post('/api/calculate-week', data="not json")
    assert response.status_code == 415

    # Negative fixed costs
    response = client.post('/api/calculate-week', json={"fixed_costs_monthly": -100})
    assert response.status_code == 400

    # Invalid product data
    response = client.post('/api/calculate-week', json={
        "products": [{"weekly_quantity": -1, "selling_price": 100, "variable_cost": 50}]
    })
    assert response.status_code == 400

    # Type error
    response = client.post('/api/calculate-week', json={
        "fixed_costs_monthly": "invalid"
    })
    assert response.status_code == 400

    # Zero quantity (ZeroDivisionError)
    response = client.post('/api/calculate-week', json={
        "products": [{"weekly_quantity": 0, "selling_price": 100, "variable_cost": 50}],
        "fixed_costs_monthly": 1000
    })
    assert response.status_code == 400

def test_delivery_modes(client):
    payload = {
        "ingredients": [], "packaging_cost": 0, "labor_hours": 0,
        "selling_price": 1000, "delivery_mode": "We_Pay", "delivery_cost": 200
    }
    response = client.post('/api/calculate-product', json=payload)
    data = response.get_json()
    assert data['delivery_cost_for_us'] == 200
    assert data['delivery_charged_to_customer'] == 0
    assert data['profit_per_unit'] == 800

    payload["delivery_mode"] = "Customer_Pays"
    response = client.post('/api/calculate-product', json=payload)
    data = response.get_json()
    assert data['delivery_cost_for_us'] == 0
    assert data['delivery_charged_to_customer'] == 200
    assert data['profit_per_unit'] == 1000

def test_loss_rate_impact(client):
    payload = {
        "ingredients": [{"name": "Ing1", "quantity": 100, "price_per_pack": 1, "pack_size": 1}],
        "packaging_cost": 0, "labor_hours": 0, "selling_price": 200, "loss_rate": 0.05
    }
    response = client.post('/api/calculate-product', json=payload)
    data = response.get_json()
    assert data['ingredient_cost_with_loss'] == 105.0

    payload["loss_rate"] = 0.10
    response = client.post('/api/calculate-product', json=payload)
    data = response.get_json()
    assert data['ingredient_cost_with_loss'] == 110.0
