import pandas as pd
import os

FILE_PATH = "csv/products.csv"

def init_products_csv():
    if not os.path.exists("csv"):
        os.makedirs("csv")
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=["Nom", "Catégorie", "Prix", "Quantité"])
        df.to_csv(FILE_PATH, index=False)

def load_products():
    init_products_csv()
    try:
        return pd.read_csv(FILE_PATH)
    except:
        return pd.DataFrame(columns=["Nom", "Catégorie", "Prix", "Quantité"])

def add_product(nom, cat, prix, qte):
    df = load_products()
    # Vérifier si le produit existe déjà
    if nom in df["Nom"].values:
        return False
    new_row = pd.DataFrame([[nom, cat, prix, qte]], columns=["Nom", "Catégorie", "Prix", "Quantité"])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)
    return True

def update_product(old_name, new_name, new_cat, new_prix, new_qte):
    """Modifie un produit existant."""
    df = load_products()
    if old_name in df["Nom"].values:
        idx = df.index[df["Nom"] == old_name][0]
        df.at[idx, "Nom"] = new_name
        df.at[idx, "Catégorie"] = new_cat
        df.at[idx, "Prix"] = new_prix
        df.at[idx, "Quantité"] = new_qte
        df.to_csv(FILE_PATH, index=False)
        return True
    return False

def delete_product(nom_produit):
    """Supprime un produit."""
    df = load_products()
    if nom_produit in df["Nom"].values:
        df = df[df["Nom"] != nom_produit]
        df.to_csv(FILE_PATH, index=False)
        return True
    return False
