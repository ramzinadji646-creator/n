# 🎂 Gestion Pâtisserie Alger - API de Gestion & Calcul de Rentabilité

## Description
Système de gestion complet pour pâtisseries à Alger. Cette application permet de digitaliser la gestion des recettes, le calcul de rentabilité, et le suivi des ventes avec une interface moderne et bilingue (Français/Arabe).

نظام إدارة كامل لمحلات الحلويات في الجزائر. يتيح هذا التطبيق رقمنة إدارة الوصفات، حساب الربحية، ومتابعة المبيعات مع واجهة حديثة وثنائية اللغة.

## Fonctionnalités Clés
- **Calcul de rentabilité avancé** : Intégration des pertes (5%), de la TVA (19%), et des tarifs saisonniers.
- **Tableau de bord interactif** : Visualisation des performances avec Chart.js.
- **Gestion des recettes** : CRUD complet avec base de données SQLite/SQLAlchemy.
- **Rapports PDF & Excel** : Génération automatique de fiches de coût et exports de données.
- **Sécurité** : Authentification JWT et protection des routes administratives.

## Installation et Lancement

1. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```
2. **Initialiser la base de données** :
   ```bash
   flask db upgrade
   python seed_data.py
   ```
3. **Lancer l'application** :
   ```bash
   python app.py
   ```
   L'application est disponible sur `http://localhost:5000`.

## Documentation des Formules

Les calculs financiers suivent exactement les règles métier spécifiées :

- **Coût matières** = Σ(quantité × prix unitaire) × (1 + taux_perte)
- **Coût variable** = matières + packaging + main d'œuvre
- **Profit** = prix_vente - coût_variable - coût_livraison_pour_nous
- **Seuil rentabilité** = charges_fixes / marge_contribution_moyenne

## API Endpoints (CURL Examples)

### 1. Calculer le coût d'un produit
```bash
curl -X POST http://localhost:5000/api/calculate-product \
     -H "Content-Type: application/json" \
     -d '{"product_name": "Gâteau Chocolat", "ingredients": [{"name": "Farine", "quantity": 1, "unit": "kg", "price": 100}], "packaging_cost": 50, "labor_hours": 1, "hourly_rate": 1500, "loss_rate": 0.05, "selling_price": 3500, "delivery_mode": "Customer_Pays", "delivery_cost": 500}'
```

### 2. Récupérer les recettes
```bash
curl -X GET http://localhost:5000/api/recipes
```

## Maintenance
- **Tests** : `pytest tests/ -v --cov`
- **Docker** : `docker-compose up --build`
