# AGENTS.md

## Project Information
- **Project Name**: Gestion Pâtisserie Alger API
- **Technology Stack**: Python 3.11, Flask, Flask-CORS
- **Currency**: DA (Dinar Algérien)
- **Business Rules**: 5% loss rate, specific delivery modes, break-even analysis.

## Build & Dev
- **Install dependencies**: `pip install -r requirements.txt`
- **Run API**: `python app.py` (Runs on port 5000)

## Testing
- **Run tests**: `pytest tests/ -v --cov`
- **Quality Gate**: Minimum 85% coverage, 0 failures.

## Data Format
- Primary data source: `data/recipes.json`
- Future expansion: Excel import using `openpyxl`.

## Style Guide
- Professional and clean code.
- Docstrings for functions.
- Multi-language error messages (FR/AR).
- Financial calculations accurate to 2 decimal places.
