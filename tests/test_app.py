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
