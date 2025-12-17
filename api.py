from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import products
import auth
import orders
import stats

app = Flask(__name__)
jwt = JWTManager(app)

# --- CONFIGURATION JWT ---
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Change ça en prod
jwt = JWTManager(app)  # <--- INDISPENSABLE : C'est ça qui active l'extension !

# --- ROUTE 1 : ACCUEIL ---
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API Groupe3 en ligne 🚀", "status": "active"})

# --- ROUTE 2 : LOGIN (Pour obtenir le Token) ---
# Sans cette route, impossible d'entrer dans les routes protégées !
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # On vérifie si username et password sont envoyés
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Champs manquants"}), 400

    username = data['username']
    password = data['password']

    # On utilise ton module auth.py pour vérifier les identifiants
    status = auth.check_login(username, password)

    if status == "OK" or status == "COMPROMISED":
        # C'est bon ! On génère le "badge d'accès" (Token)
        access_token = create_access_token(identity=username)
        return jsonify({
            "message": "Connexion réussie", 
            "token": access_token,
            "security_warning": (status == "COMPROMISED")
        }), 200
    else:
        return jsonify({"error": "Identifiants incorrects"}), 401

# --- ROUTE 3 : LISTE DES PRODUITS (Publique) ---
@app.route('/api/products', methods=['GET'])
def get_all_products():
    df = products.load_products()
    # Gestion du cas où le fichier est vide ou corrompu
    if df.empty:
        return jsonify([])
    # Remplacement des NaN (valeurs vides) par None pour que le JSON soit valide
    df = df.where(pd.notnull(df), None)
    data = df.to_dict(orient='records')
    return jsonify(data)

# --- ROUTE 4 : CRÉATION PRODUIT (Protégée) ---
@app.route('/api/products', methods=['POST'])
@jwt_required()  # <--- Il faut le Token pour entrer ici
def create_product():
    # Qui est connecté ?
    current_user = get_jwt_identity()
    
    # (Optionnel) Tu pourrais vérifier si c'est l'admin ici
    # if current_user != "admin": return jsonify({"error": "Interdit"}), 403

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
    else:
        return jsonify({"error": "Produit déjà existant"}), 409

# --- ROUTE 5 : MODIFIER UN PRODUIT (PUT) ---
@app.route('/api/products/<string:product_name>', methods=['PUT'])
@jwt_required() # Sécurisé !
def update_product_endpoint(product_name):
    # 1. On récupère les nouvelles données
    data = request.get_json()
    
    # 2. On vérifie qu'on a bien reçu quelque chose
    if not data:
        return jsonify({"error": "Aucune donnée envoyée"}), 400
        
    # 3. On charge les produits pour récupérer les anciennes valeurs (si besoin)
    #    Astuce : Si l'utilisateur n'envoie pas le prix, on pourrait garder l'ancien.
    #    Pour simplifier ici, on exige que l'utilisateur renvoie tout.
    
    succes = products.update_product(
        product_name, # Le nom actuel (celui dans l'URL)
        data.get('nom', product_name), # Nouveau nom (ou garde l'ancien)
        data.get('catégorie', 'Non classé'),
        data.get('prix', 0),
        data.get('quantité', 0)
    )
    
    if succes:
        return jsonify({"message": f"Produit '{product_name}' mis à jour !"}), 200
    else:
        return jsonify({"error": "Produit introuvable"}), 404

# --- ROUTE 6 : SUPPRIMER UN PRODUIT (DELETE) ---
@app.route('/api/products/<string:product_name>', methods=['DELETE'])
@jwt_required() # Sécurisé !
def delete_product_endpoint(product_name):
    # Appel de la fonction de suppression
    succes = products.delete_product(product_name)
    
    if succes:
        return jsonify({"message": f"Produit '{product_name}' supprimé."}), 200
    else:
        return jsonify({"message": f"erreur ouais ouais ouais"}), 404
    
   # --- ROUTE 7 : DÉTAILS D'UN PRODUIT (GET) ---
@app.route('/api/products/<string:product_name>', methods=['GET'])
def get_product_detail(product_name):
    
    # Appel de la fonction de recherche
    infos_produit = products.get_product(product_name)
    
    if infos_produit:
        # Si trouvé, on renvoie le JSON du produit
        return jsonify(infos_produit), 200
    else:
        # Si pas trouvé
        return jsonify({"error": "Produit introuvable"}), 404
    

@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    # Optionnel : On pourrait filtrer pour que l'utilisateur ne voie que SES commandes.
    # Ici, on fait simple : on affiche tout.
    df = orders.load_orders()
    if df.empty:
        return jsonify([])
    return jsonify(df.to_dict(orient='records')), 200

# --- ROUTE 9 : PASSER UNE COMMANDE (POST) ---
@app.route('/api/orders', methods=['POST'])
@jwt_required()
def add_order():
    # 1. Qui est connecté ?
    current_user = get_jwt_identity()
    
    # 2. Que veut-il acheter ?
    data = request.get_json()
    if not data or 'produit' not in data or 'quantité' not in data:
        return jsonify({"error": "Il faut 'produit' et 'quantité'"}), 400
        
    nom_prod = data['produit']
    qty = int(data['quantité'])
    
    if qty <= 0:
        return jsonify({"error": "La quantité doit être positive"}), 400

    # 3. Action !
    succes, message = orders.create_order(current_user, nom_prod, qty), 'oeoeoe'
    
    if succes:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 409 # 409 = Conflit (stock)


# --- ROUTE 10 : STATISTIQUES (GET) ---
@app.route('/api/stats', methods=['GET'])
@jwt_required() # Réservé aux admins connectés
def get_stats():
    # Appel de la fonction de calcul
    data = stats.get_global_stats()
    
    return jsonify(data), 200

# --- LANCEMENT ---
if __name__ == '__main__':
    # On importe pandas ici seulement si besoin pour éviter les erreurs circulaires si mal placé
    import pandas as pd 
    app.run(debug=True, port=5000)


    