import os
from flask import Flask
from app.extensions import db, migrate, jwt, bcrypt, cors, limiter, csrf
from app.config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # Exempt API from CSRF if using JWT in headers, but let's keep it for security
    # unless we hit issues. For now, let's just initialize it.

    # Import models to register them with SQLAlchemy
    from app import models

    # Register blueprints
    from app.blueprints.api import api_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(main_bp)

    from flask_swagger_ui import get_swaggerui_blueprint
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    swagger_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Pâtisserie Alger API"})
    app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)

    return app
