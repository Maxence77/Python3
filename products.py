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
    df = df[df["Nom"] != nom_produit]
    df.to_csv(PRODUCTS_FILE, index=False)

def update_stock(nom_produit, qty_vendue):
    """Module 5: Décrément automatique du stock"""
    df = load_products()
    idx = df.index[df["Nom"] == nom_produit].tolist()
    if idx:
        current_qty = df.at[idx[0], "Quantité"]
        df.at[idx[0], "Quantité"] = current_qty - qty_vendue
        df.to_csv(PRODUCTS_FILE, index=False)