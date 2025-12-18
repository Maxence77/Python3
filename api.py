"""
Module principal de l'API Flask (CORRIGÉ).

Gère l'authentification, les produits, les commandes et les statistiques.
Intègre la gestion des mots de passe compromis (Pwned API).
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

# Chargement des variables d'environnement (.env)
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION SÉCURISÉE ---
# Récupération de la clé depuis le .env
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback-dev-key")

jwt = JWTManager(app)


# --- UTILITAIRES ---
def is_valid_username(username):
    """
    Vérifie que le nom d'utilisateur ne contient que :
    - Lettres (a-z, A-Z)
    - Chiffres (0-9)
    - Underscore (_)
    """
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None


# --- ROUTE 1 : ACCUEIL ---
@app.route('/', methods=['GET'])
def home():
    """Route d'accueil pour vérifier que l'API est en ligne."""
    return jsonify({"message": "API Groupe3 en ligne 🚀", "status": "active"})


# --- ROUTE 2 : LOGIN (CORRIGÉE) ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Authentifie un utilisateur et retourne un token JWT + statut admin.
    Gère le cas "WARNING" (mot de passe piraté).
    """
    data = request.get_json()

    # 1. Vérification des champs requis
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Champs manquants"}), 400

    username = data['username']
    password = data['password']

    # 2. Validation format username
    if not is_valid_username(username):
        return jsonify({
            "error": "Format invalide. Utilisez uniquement lettres, chiffres et '_'"
        }), 400

    # 3. Authentification via auth.py
    # CORRECTION IMPORTANTE : On récupère 3 valeurs (status, is_admin, token_interne)
    status, is_admin, _ = auth.authenticate_user(username, password)

    # Cas A : Succès complet ou Succès avec Avertissement
    if status in ["SUCCESS", "WARNING"]:
        access_token = create_access_token(identity=username)
        
        response = {
            "message": "Connexion réussie",
            "token": access_token,
            "is_admin": is_admin
        }
        
        # Si le mot de passe est compromis, on ajoute une alerte dans le JSON
        if status == "WARNING":
            response["alert"] = "⚠️ SÉCURITÉ : Votre mot de passe est compromis (Pwned API). Changez-le rapidement."
            
        return jsonify(response), 200

    # Cas B : Échec
    return jsonify({"error": "Identifiants incorrects"}), 401


# --- ROUTE 3 : LISTE DES PRODUITS ---
@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Retourne la liste de tous les produits."""
    df_products = products.load_products()

    if df_products.empty:
        return jsonify([])

    # Nettoyage des valeurs NaN pour le JSON
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

    # On appelle la fonction update de products.py
    # Note : assure-toi que products.update_product ou update_product_full est bien aligné
    succes = products.update_product(
        product_name,
        data.get('nom', product_name),
        data.get('catégorie', 'Non classé'),
        data.get('prix', 0),
        data.get('quantité', 0)
    )

    if succes:
        return jsonify({"message": f"Produit '{product_name}' mis à jour !"}), 200
    return jsonify({"error": "Produit introuvable ou erreur de mise à jour"}), 404


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
    
    # Nettoyage NaN
    df_orders = df_orders.where(pd.notnull(df_orders), None)
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
    # Mode debug activé pour le développement
    app.run(debug=True, port=5000)