"""
Module de gestion du catalogue produits pour l'ERP.
Permet l'initialisation, le chargement, l'ajout et la modification des produits en CSV.
"""

import os
import pandas as pd

FILE_PATH = "csv/products.csv"


def init_products_csv():
    """Initialise le dossier csv et le fichier products.csv s'ils n'existent pas."""
    if not os.path.exists("csv"):
        os.makedirs("csv")
    if not os.path.exists(FILE_PATH):
        columns = ["Nom", "Catégorie", "Prix", "Quantité"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(FILE_PATH, index=False)


def load_products():
    """Charge les produits depuis le CSV et retourne un DataFrame."""
    init_products_csv()
    try:
        return pd.read_csv(FILE_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["Nom", "Catégorie", "Prix", "Quantité"])


def add_product(nom, cat, prix, qte):
    """Ajoute un nouveau produit au catalogue après avoir vérifié son existence."""
    df = load_products()
    if nom in df["Nom"].values:
        return False
    cols = ["Nom", "Catégorie", "Prix", "Quantité"]
    new_row = pd.DataFrame([[nom, cat, prix, qte]], columns=cols)
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)
    return True


def update_product(old_name, new_name, new_cat, new_prix, new_qte):
    """Modifie les informations d'un produit existant."""
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
    """Supprime un produit du catalogue selon son nom."""
    df = load_products()
    if nom_produit in df["Nom"].values:
        df = df[df["Nom"] != nom_produit]
        df.to_csv(FILE_PATH, index=False)
        return True
    return False
