# 🎂 Gestion Pâtisserie Alger - API de Gestion & Calcul de Rentabilité

## Description (FR/AR)
Système de gestion pour pâtisserie à Alger. Ce projet permet de digitaliser la gestion des coûts et du profit pour une pâtisserie, en calculant la rentabilité par produit et par semaine.

نظام إدارة محلات الحلويات في الجزائر. يسمح هذا المشروع برقمنة إدارة التكاليف والأرباح لمحل حلويات، مع حساب الربحية لكل منتج وأسبوعياً.

## Installation
1. Clonez le dépôt.
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Run / Exécution
Pour lancer l'API :
```bash
python app.py
```
L'API sera disponible sur `http://localhost:5000`.

## API Documentation

### 1. POST `/api/calculate-product`
Calcule le coût et le profit d'un produit.
**Exemple cURL :**
```bash
curl -X POST http://localhost:5000/api/calculate-product -H "Content-Type: application/json" -d '{
  "product_name": "Gâteau Chocolat",
  "ingredients": [
    {"name": "Farine", "quantity": 0.5, "price_per_pack": 100, "pack_size": 1},
    {"name": "Sucre", "quantity": 0.2, "price_per_pack": 50, "pack_size": 0.5}
  ],
  "packaging_cost": 100,
  "labor_hours": 1.5,
  "selling_price": 3500,
  "delivery_mode": "Customer_Pays",
  "delivery_cost": 500
}'
```

### 2. POST `/api/calculate-week`
Analyse hebdomadaire et seuil de rentabilité.
**Exemple cURL :**
```bash
curl -X POST http://localhost:5000/api/calculate-week -H "Content-Type: application/json" -d '{
  "products": [
    {"name": "Gâteau Chocolat", "selling_price": 3500, "variable_cost": 2507.5, "weekly_quantity": 10}
  ],
  "fixed_costs_monthly": 21000
}'
```

### 3. GET `/api/recipes`
Récupère les recettes prédéfinies.

### 4. GET `/api/health`
Vérification de l'état du système.

## Formules (Formulas)
- **Coût matières** = Σ(quantité × prix unitaire) × (1 + taux_perte)
- **Coût variable** = matières + packaging + main d'œuvre
- **Profit** = prix_vente - coût_variable - coût_livraison_pour_nous
- **Seuil rentabilité** = charges_fixes / marge_contribution_moyenne

## Exemple de calcul (Walkthrough)
Pour un gâteau avec 150 DA d'ingrédients, 5% de perte, 100 DA de packaging et 2250 DA de main d'œuvre :
1. Coût matières avec perte = 150 * 1.05 = 157.5 DA
2. Coût variable = 157.5 + 100 + 2250 = 2507.5 DA
3. Si prix de vente = 3500 DA et livraison payée par le client :
   Profit = 3500 - 2507.5 - 0 = 992.5 DA
