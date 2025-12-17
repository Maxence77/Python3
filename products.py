import pandas as pd
import os

CSV_FOLDER = "csv"
PRODUCTS_FILE = os.path.join(CSV_FOLDER, "products.csv")

if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        df = pd.DataFrame(columns=["Nom", "Catégorie", "Prix", "Quantité", "Date Ajout"])
        df.to_csv(PRODUCTS_FILE, index=False)
        return df
    return pd.read_csv(PRODUCTS_FILE)

def add_product(nom, categorie, prix, quantite):
    df = load_products()
    # Si le produit existe déjà, on ne l'ajoute pas (ou on pourrait additionner)
    if nom in df["Nom"].values:
        return False
    
    new_data = pd.DataFrame([{
        "Nom": nom,
        "Catégorie": categorie,
        "Prix": float(prix),
        "Quantité": int(quantite),
        "Date Ajout": pd.Timestamp.now().strftime('%Y-%m-%d')
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(PRODUCTS_FILE, index=False)
    return True

def update_product(old_name, new_name, new_cat, new_price, new_qty):
    """Module 4: Édition inline / Mise à jour"""
    df = load_products()
    idx = df.index[df["Nom"] == old_name].tolist()
    if idx:
        i = idx[0]
        df.at[i, "Nom"] = new_name
        df.at[i, "Catégorie"] = new_cat
        df.at[i, "Prix"] = float(new_price)
        df.at[i, "Quantité"] = int(new_qty)
        df.to_csv(PRODUCTS_FILE, index=False)
        return True
    return False

def delete_product(nom_produit):
    df = load_products()
    
    # 1. Sécurité : Si le dataframe est vide, on s'arrête
    if df.empty:
        return False

    # 2. CONVERSION : On force la colonne "Nom" à être du texte (str)
    #    Ça règle le problème si le nom était un nombre (ex: 123)
    df["Nom"] = df["Nom"].astype(str)
    
    # 3. NETTOYAGE : On enlève les espaces invisibles avant/après dans le CSV
    df["Nom"] = df["Nom"].str.strip()
    
    # 4. NETTOYAGE : On enlève les espaces du nom reçu
    cible = str(nom_produit).strip()
    
    # 5. Vérification
    if cible in df["Nom"].values:
        # On garde tout ce qui n'est PAS la cible
        df = df[df["Nom"] != cible]
        df.to_csv(PRODUCTS_FILE, index=False)
        return True
        
    return False

def update_stock(nom_produit, qty_vendue):
    """Module 5: Décrément automatique du stock"""
    df = load_products()
    idx = df.index[df["Nom"] == nom_produit].tolist()
    if idx:
        current_qty = df.at[idx[0], "Quantité"]
        df.at[idx[0], "Quantité"] = current_qty - qty_vendue
        df.to_csv(PRODUCTS_FILE, index=False)

def get_product(nom_produit):
    """Cherche un produit spécifique et retourne ses infos ou None."""
    df = load_products()
    
    if df.empty:
        return None

    # Nettoyage pour comparaison fiable
    df["Nom"] = df["Nom"].astype(str).str.strip()
    cible = str(nom_produit).strip()
    
    # Filtrage
    resultat = df[df["Nom"] == cible]
    
    if not resultat.empty:
        # On retourne la première ligne trouvée sous forme de dictionnaire
        return resultat.iloc[0].to_dict()
    
    return None