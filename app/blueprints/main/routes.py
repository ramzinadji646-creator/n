from flask import render_template
from app.blueprints.main import main_bp

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/calculator')
def calculator():
    return render_template('calculator.html')

@main_bp.route('/recipes')
def recipes():
    return render_template('recipes.html')

@main_bp.route('/orders')
def orders():
    return render_template('orders.html')

@main_bp.route('/login')
def login():
    return render_template('auth/login.html')

@main_bp.route('/register')
def register():
    return render_template('auth/register.html')
