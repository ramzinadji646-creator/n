# AGENTS.md

## Project Information
- **Project Name**: Gestion Pâtisserie Alger API
- **Technology Stack**: Python 3.11, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS
- **Currency**: DA (Dinar Algérien)
- **Business Rules**:
  - 5% loss rate default.
  - Delivery modes: `Customer_Pays` (0 cost to us) vs `We_Pay` (fixed cost to us).
  - Seasonal pricing (Summer +10% cost).
  - Bulk discounts (10+ units: -5%, 50+ units: -10%).
  - TVA: 19% applied to total cost where applicable.

## Build & Dev
- **Dependencies**: `pip install -r requirements.txt`
- **Database**: `flask db upgrade` followed by `python seed_data.py`.
- **Run**: `python app.py` (Default port: 5000).
- **Docker**: `docker-compose up`.

## Testing
- **Framework**: `pytest`
- **Command**: `pytest tests/ -v --cov`
- **Quality Gate**: Minimum 85% coverage, 0 failures. (Current: 96%)

## Data Format
- Primary storage: SQLite (`app.db`).
- Seed data: `data/recipes.json` & `seed_data.py`.
- Exports: Excel (`openpyxl`) and PDF (`reportlab`).

## Style Guide
- Professional and clean code with type hints.
- Arabic (RTL) support for UI.
- Docstrings for all services and models.
- Financial calculations rounded to 2 decimal places.
