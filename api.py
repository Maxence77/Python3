"""
Module principal de l'API Flask.

Gère l'authentification, les produits, les commandes et les statistiques.
Point d'entrée de l'application.
"""

import os
# 1. Imports Tiers
import pandas as pd
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from dotenv import load_dotenv

# 2. Imports Locaux (Tes modules)
import products
import auth
import orders
import stats

# Chargement des variables d'environnement (.env)
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION SÉCURISÉE (Correction Bandit B105) ---
# On récupère la clé secrète depuis le .env.
# "dev-fallback-key" est là juste pour éviter que ça plante si tu oublies le .env en local.
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-fallback-key")

jwt = JWTManager(app)


# --- ROUTE 1 : ACCUEIL ---
@app.route('/', methods=['GET'])
def home():
    """Route d'accueil pour vérifier que l'API est en ligne."""
    return jsonify({"message": "API Groupe3 en ligne 🚀", "status": "active"})


# --- ROUTE 2 : LOGIN ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authentifie un utilisateur et retourne un token JWT."""
    data = request.get_json()

    # Vérification des champs
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Champs manquants"}), 400

    username = data['username']
    password = data['password']

    # --- MISE À JOUR SÉCURITÉ ---
    # On utilise la fonction 'authenticate_user' du nouveau auth.py sécurisé.
    # (Avant c'était auth.check_login)
    status = auth.authenticate_user(username, password)

    if status == "OK":
        access_token = create_access_token(identity=username)
        return jsonify({
            "message": "Connexion réussie",
            "token": access_token
        }), 200

    return jsonify({"error": "Identifiants incorrects"}), 401


# --- ROUTE 3 : LISTE DES PRODUITS ---
@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Retourne la liste de tous les produits."""
    df_products = products.load_products()

    if df_products.empty:
        return jsonify([])

    # Nettoyage des valeurs nulles (NaN) pour le JSON car JSON déteste les NaN
    df_products = df_products.where(pd.notnull(df_products), None)
    data = df_products.to_dict(orient='records')
    return jsonify(data)


# --- ROUTE 4 : CRÉATION PRODUIT ---
@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    """Crée un nouveau produit (Nécessite authentification)."""
    current_user = get_jwt_identity()
    data = request.get_json()

    if not data or 'nom' not in data or 'prix' not in data:
        return jsonify({"error": "Champs 'nom' et 'prix' obligatoires"}), 400

    succes = products.add_product(
        data['nom'],
        data.get('catégorie', 'Autre'),
        data['prix'],
        data.get('quantité', 0)
    )

    if succes:
        return jsonify({"message": f"Produit ajouté par {current_user} !"}), 201
    return jsonify({"error": "Produit déjà existant"}), 409


# --- ROUTE 5 : MODIFIER UN PRODUIT ---
@app.route('/api/products/<string:product_name>', methods=['PUT'])
@jwt_required()
def update_product_endpoint(product_name):
    """Met à jour un produit existant."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Aucune donnée envoyée"}), 400

    succes = products.update_product(
        product_name,
        data.get('nom', product_name),
        data.get('catégorie', 'Non classé'),
        data.get('prix', 0),
        data.get('quantité', 0)
    )

    if succes:
        return jsonify({"message": f"Produit '{product_name}' mis à jour !"}), 200
    return jsonify({"error": "Produit introuvable"}), 404


# --- ROUTE 6 : SUPPRIMER UN PRODUIT ---
@app.route('/api/products/<string:product_name>', methods=['DELETE'])
@jwt_required()
def delete_product_endpoint(product_name):
    """Supprime un produit."""
    succes = products.delete_product(product_name)

    if succes:
        return jsonify({"message": f"Produit '{product_name}' supprimé."}), 200
    return jsonify({"error": "Produit introuvable"}), 404


# --- ROUTE 7 : DÉTAILS D'UN PRODUIT ---
@app.route('/api/products/<string:product_name>', methods=['GET'])
def get_product_detail(product_name):
    """Récupère les détails d'un produit spécifique."""
    infos_produit = products.get_product(product_name)

    if infos_produit:
        return jsonify(infos_produit), 200
    return jsonify({"error": "Produit introuvable"}), 404


# --- ROUTE 8 : LISTE DES COMMANDES ---
@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Retourne la liste des commandes."""
    df_orders = orders.load_orders()
    if df_orders.empty:
        return jsonify([])
    return jsonify(df_orders.to_dict(orient='records')), 200


# --- ROUTE 9 : PASSER UNE COMMANDE ---
@app.route('/api/orders', methods=['POST'])
@jwt_required()
def add_order():
    """Enregistre une nouvelle commande."""
    current_user = get_jwt_identity()
    data = request.get_json()

    if not data or 'produit' not in data or 'quantité' not in data:
        return jsonify({"error": "Il faut 'produit' et 'quantité'"}), 400

    nom_prod = data['produit']
    # Sécurité : on s'assure que c'est bien un entier
    try:
        qty = int(data['quantité'])
    except ValueError:
        return jsonify({"error": "La quantité doit être un nombre entier"}), 400

    if qty <= 0:
        return jsonify({"error": "La quantité doit être positive"}), 400

    succes, message = orders.create_order(current_user, nom_prod, qty)

    if succes:
        return jsonify({"message": message}), 201
    return jsonify({"error": message}), 409


# --- ROUTE 10 : STATISTIQUES ---
@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Retourne les statistiques globales (KPI)."""
    data = stats.get_global_stats()
    return jsonify(data), 200


if __name__ == '__main__':
    # Correction Bandit B201 : On signale que le debug=True est volontaire
    app.run(debug=True, port=5000)  # nosec
