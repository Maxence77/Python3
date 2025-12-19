"""
Module principal de l'API Flask.

Gère l'authentification, les produits, les commandes et les statistiques.
Intègre la gestion des mots de passe compromis via l'API Pwned.
"""

import os
import re
import pandas as pd
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from dotenv import load_dotenv

# Imports Locaux
import products
import auth
import orders
import stats

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION SÉCURISÉE ---
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback-dev-key")
jwt = JWTManager(app)


def is_valid_username(username):
    """
    Vérifie que le nom d'utilisateur respecte le format alphanumérique.
    """
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None


@app.route('/', methods=['GET'])
def home():
    """Route d'accueil."""
    return jsonify({"message": "API Groupe3 en ligne 🚀", "status": "active"})


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authentifie un utilisateur et retourne un token JWT."""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Champs manquants"}), 400

    username = data['username']
    password = data['password']

    if not is_valid_username(username):
        return jsonify({
            "error": "Format invalide. Utilisez uniquement lettres, chiffres et '_'"
        }), 400

    # On ignore la 3ème valeur (token_interne) avec underscore
    status, is_admin, _ = auth.authenticate_user(username, password)

    if status in ["SUCCESS", "WARNING"]:
        access_token = create_access_token(identity=username)
        response_data = {
            "message": "Connexion réussie",
            "token": access_token,
            "is_admin": is_admin
        }

        if status == "WARNING":
            response_data["alert"] = "⚠️ SÉCURITÉ : Mot de passe compromis. Changez-le."

        return jsonify(response_data), 200

    return jsonify({"error": "Identifiants incorrects"}), 401


@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Retourne la liste de tous les produits."""
    df_products = products.load_products()

    if df_products.empty:
        return jsonify([])

    # Remplace les NaN par None pour la compatibilité JSON
    df_products = df_products.where(pd.notnull(df_products), None)
    return jsonify(df_products.to_dict(orient='records'))


@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    """Crée un nouveau produit."""
    current_user = get_jwt_identity()
    data = request.get_json()

    if not data or 'nom' not in data or 'prix' not in data:
        return jsonify({"error": "Champs 'nom' et 'prix' obligatoires"}), 400

    success = products.add_product(
        data['nom'],
        data.get('catégorie', 'Autre'),
        data['prix'],
        data.get('quantité', 0)
    )

    if success:
        return jsonify({"message": f"Produit ajouté par {current_user} !"}), 201
    return jsonify({"error": "Produit déjà existant"}), 409


@app.route('/api/products/<string:product_name>', methods=['PUT'])
@jwt_required()
def update_product_endpoint(product_name):
    """Met à jour un produit existant."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Aucune donnée envoyée"}), 400

    success = products.update_product(
        product_name,
        data.get('nom', product_name),
        data.get('catégorie', 'Non classé'),
        data.get('prix', 0),
        data.get('quantité', 0)
    )

    if success:
        return jsonify({"message": f"Produit '{product_name}' mis à jour !"}), 200
    return jsonify({"error": "Produit introuvable"}), 404


@app.route('/api/products/<string:product_name>', methods=['DELETE'])
@jwt_required()
def delete_product_endpoint(product_name):
    """Supprime un produit."""
    if products.delete_product(product_name):
        return jsonify({"message": f"Produit '{product_name}' supprimé."}), 200
    return jsonify({"error": "Produit introuvable"}), 404


@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Retourne la liste des commandes."""
    df_orders = orders.load_orders()
    if df_orders.empty:
        return jsonify([])

    df_orders = df_orders.where(pd.notnull(df_orders), None)
    return jsonify(df_orders.to_dict(orient='records')), 200


@app.route('/api/orders', methods=['POST'])
@jwt_required()
def add_order():
    """Enregistre une nouvelle commande."""
    current_user = get_jwt_identity()
    data = request.get_json()

    if not data or 'produit' not in data or 'quantité' not in data:
        return jsonify({"error": "Champs manquants"}), 400

    try:
        qty = int(data['quantité'])
        if qty <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "La quantité doit être un entier positif"}), 400

    success, message = orders.create_order(current_user, data['produit'], qty)

    if success:
        return jsonify({"message": message}), 201
    return jsonify({"error": message}), 409


@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Retourne les statistiques globales."""
    return jsonify(stats.get_global_stats()), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
