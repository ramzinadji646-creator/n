import pytest
import json
from app import create_app
from app.extensions import db
from app.models import User, Ingredient, Recipe, Order, Product

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client, app):
    with app.app_context():
        user = User(username="admin", email="admin@example.com", role="admin")
        user.set_password("adminpassword")
        db.session.add(user)
        db.session.commit()

    res = client.post('/api/auth/login', json={
        "username": "admin",
        "password": "adminpassword"
    })
    return res.get_json()['access_token']

def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200

def test_auth_full(client):
    # Register
    res = client.post('/api/auth/register', json={"username": "u1", "email": "e1@e.com", "password": "p1"})
    assert res.status_code == 201
    # Login
    res = client.post('/api/auth/login', json={"username": "u1", "password": "p1"})
    token = res.get_json()['access_token']
    # Me
    res = client.get('/api/auth/me', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    # Logout
    res = client.post('/api/auth/logout', headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

    # Error cases
    res = client.post('/api/auth/register', json={})
    assert res.status_code == 400
    res = client.post('/api/auth/login', json={})
    assert res.status_code == 400

def test_ingredients_api(client, admin_token):
    # Add
    res = client.post('/api/ingredients', json={"name": "I1"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    # Error add
    res = client.post('/api/ingredients', json={}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 400
    # List
    res = client.get('/api/ingredients')
    assert len(res.get_json()['ingredients']) == 1

def test_recipes_api(client, admin_token):
    # Add ingredient
    res = client.post('/api/ingredients', json={"name": "I1"}, headers={"Authorization": f"Bearer {admin_token}"})
    iid = res.get_json()['id']
    # Add recipe
    res = client.post('/api/recipes', json={
        "name": "R1",
        "selling_price": 1000,
        "ingredients": [{"ingredient_id": iid, "quantity": 1}]
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    rid = res.get_json()['id']
    # Get recipe
    res = client.get(f'/api/recipes/{rid}')
    assert res.status_code == 200

def test_backward_compat_api(client):
    # calculate-product
    payload = {"selling_price": 1000, "labor_hours": 1}
    res = client.post('/api/calculate-product', json=payload)
    assert res.status_code == 200
    # calculate-week
    payload = {"products": [{"weekly_quantity": 10, "selling_price": 1000, "variable_cost": 500}]}
    res = client.post('/api/calculate-week', json=payload)
    assert res.status_code == 200

def test_stats_and_export(client, admin_token):
    client.get('/api/stats/daily', headers={"Authorization": f"Bearer {admin_token}"})
    client.get('/api/export/recipes/excel')

def test_orders_api(client, admin_token):
    # Need product (Recipe)
    from app.models import Recipe
    with client.application.app_context():
        r = Recipe(name="R_Order_Test", selling_price=1000)
        db.session.add(r)
        db.session.commit()
        rid = r.id

    # POST
    res = client.post('/api/orders', json={
        "product_id": rid,
        "quantity": 1,
        "total_price": 1000,
        "customer_name": "Test Client"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    oid = res.get_json()['id']

    # GET
    res = client.get('/api/orders')
    assert res.status_code == 200

    # PUT
    res = client.put(f'/api/orders/{oid}', json={"status": "Completed"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

    # DELETE
    res = client.delete(f'/api/orders/{oid}', headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

def test_main_views(client):
    for route in ['/', '/dashboard', '/calculator', '/recipes', '/orders', '/login', '/register']:
        assert client.get(route).status_code == 200

def test_pdf_report_gen(client):
    from app.services.report_service import ReportService
    stats = {
        "revenue": 1000,
        "profit": 500,
        "products": [{"name": "P1", "quantity": 1, "revenue": 1000}]
    }
    pdf = ReportService.generate_weekly_pdf(stats)
    assert pdf.getvalue().startswith(b'%PDF')

def test_export_recipe_pdf_endpoint(client, admin_token):
    # Need a recipe
    res = client.post('/api/ingredients', json={"name": "I1"}, headers={"Authorization": f"Bearer {admin_token}"})
    iid = res.get_json()['id']
    res = client.post('/api/recipes', json={
        "name": "R1_PDF_Test",
        "selling_price": 1000,
        "ingredients": [{"ingredient_id": iid, "quantity": 1}]
    }, headers={"Authorization": f"Bearer {admin_token}"})
    rid = res.get_json()['id']

    res = client.get(f'/api/export/recipe/{rid}/pdf')
    assert res.status_code == 200
    assert res.data.startswith(b'%PDF')

def test_dashboard_api_endpoints(client, admin_token):
    # Setup some data
    res = client.post('/api/recipes', json={
        "name": "Cake",
        "selling_price": 1000,
        "ingredients": []
    }, headers={"Authorization": f"Bearer {admin_token}"})
    rid = res.get_json()['id']

    order_data = {
        "customer_name": "Test Client",
        "product_id": rid,
        "quantity": 2,
        "total_price": 2000,
        "status": "Pending"
    }
    client.post('/api/orders', json=order_data, headers={"Authorization": f"Bearer {admin_token}"})

    # Test stats
    res = client.get('/api/dashboard/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert 'revenue_today' in data
    assert data['revenue_today'] == 2000

    # Test recent orders
    res = client.get('/api/dashboard/recent-orders')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['orders']) > 0

    # Test revenue trend
    res = client.get('/api/dashboard/revenue-trend')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['labels']) == 7

    # Test top products
    res = client.get('/api/dashboard/top-products')
    assert res.status_code == 200
    data = res.get_json()
    assert 'labels' in data

    # Test single order GET
    res = client.get(f'/api/orders/1')
    assert res.status_code == 200
    assert res.get_json()['customer_name'] == "Test Client"

    # Test print order (HTML)
    res = client.get(f'/api/orders/1/print')
    assert res.status_code == 200
    assert b"BON DE COMMANDE #1" in res.data

def test_api_error_cases(client, admin_token):
    # Non-existent recipe
    res = client.get('/api/recipes/999')
    assert res.status_code == 404

    # Non-existent order
    res = client.get('/api/orders/999')
    assert res.status_code == 404

    # Non-existent print
    res = client.get('/api/orders/999/print')
    assert res.status_code == 404

    # Missing product in calculate
    res = client.post('/api/calculate-product', json={})
    assert res.status_code == 400

    # Recipe with no name
    res = client.post('/api/recipes', json={"selling_price": 100}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 400

def test_unauthorized_actions(client):
    # Try to delete order without token
    res = client.delete('/api/orders/1')
    assert res.status_code == 401

    # Try to add recipe without token
    res = client.post('/api/recipes', json={"name": "NoToken"})
    assert res.status_code == 401

def test_ingredient_deletion(client, admin_token):
    res = client.post('/api/ingredients', json={"name": "DeleteMe"}, headers={"Authorization": f"Bearer {admin_token}"})
    iid = res.get_json()['id']
    res = client.delete(f'/api/ingredients/{iid}', headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

def test_recipe_update(client, admin_token):
    res = client.post('/api/recipes', json={"name": "OldName", "selling_price": 100}, headers={"Authorization": f"Bearer {admin_token}"})
    rid = res.get_json()['id']
    res = client.put(f'/api/recipes/{rid}', json={"name": "NewName"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert client.get(f'/api/recipes/{rid}').get_json()['name'] == "NewName"

def test_ingredients_advanced(client, admin_token):
    # Search
    client.post('/api/ingredients', json={"name": "SearchMe"}, headers={"Authorization": f"Bearer {admin_token}"})
    res = client.get('/api/ingredients?q=SearchMe')
    assert len(res.get_json()['ingredients']) == 1

    # Pagination
    res = client.get('/api/ingredients?page=1&per_page=1')
    assert len(res.get_json()['ingredients']) == 1

    # Update
    res = client.post('/api/ingredients', json={"name": "ToUpdate"}, headers={"Authorization": f"Bearer {admin_token}"})
    iid = res.get_json()['id']
    res = client.put(f'/api/ingredients/{iid}', json={"name": "UpdatedName", "price_per_pack": 500}, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.get_json()['name'] == "UpdatedName"

def test_recipe_advanced(client, admin_token):
    # Search
    client.post('/api/recipes', json={"name": "RecipeSearch", "selling_price": 100}, headers={"Authorization": f"Bearer {admin_token}"})
    res = client.get('/api/recipes?q=RecipeSearch')
    assert len(res.get_json()) >= 1

    # Update with ingredients
    ing_res = client.post('/api/ingredients', json={"name": "Ing1"}, headers={"Authorization": f"Bearer {admin_token}"})
    iid = ing_res.get_json()['id']
    rec_res = client.post('/api/recipes', json={"name": "RecUpdate", "selling_price": 200}, headers={"Authorization": f"Bearer {admin_token}"})
    rid = rec_res.get_json()['id']

    res = client.put(f'/api/recipes/{rid}', json={
        "ingredients": [{"ingredient_id": iid, "quantity": 5}]
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

    # Delete
    res = client.delete(f'/api/recipes/{rid}', headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

def test_stats_extended(client, admin_token):
    client.get('/api/stats/weekly')
    client.get('/api/stats/monthly')
    client.get('/api/stats/top-products')
    client.get('/api/stats/trends')

def test_orders_advanced(client, admin_token):
    # Need recipe
    res = client.post('/api/recipes', json={"name": "OrderRec", "selling_price": 1000}, headers={"Authorization": f"Bearer {admin_token}"})
    rid = res.get_json()['id']

    # Post with delivery date and phone
    payload = {
        "customer_name": "Adv Client",
        "customer_phone": "123456",
        "product_id": rid,
        "quantity": 3,
        "delivery_date": "2026-01-01",
        "notes": "Fast please"
    }
    res = client.post('/api/orders', json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 201
    oid = res.get_json()['id']

    # Put with notes and phone
    res = client.put(f'/api/orders/{oid}', json={
        "notes": "Changed note",
        "customer_phone": "654321",
        "delivery_date": "2026-02-02",
        "quantity": 4,
        "total_price": 4000
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert res.get_json()['order']['notes'] == "Changed note"

def test_products_api(client):
    res = client.get('/api/products')
    assert res.status_code == 200
