"""
Module de gestion du catalogue produits pour l'ERP.
Permet l'initialisation, le chargement, l'ajout et la modification des produits en CSV.
"""

import os
import re
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
    """Ajoute un nouveau produit au catalogue après avoir vérifié son existence et validé les données."""
    
    # 1. Validation Backend (Regex) - Sécurité supplémentaire
    if not isinstance(nom, str) or not re.match(r'^[a-zA-Z\s]+$', nom):
        return False, "Nom invalide (Lettres uniquement)"
    
    if not isinstance(cat, str) or not re.match(r'^[a-zA-Z0-9\s]+$', cat):
        # On autorise chiffres et lettres pour la catégorie
        return False, "Catégorie invalide (Pas de caractères spéciaux)"
        
    try:
        f_prix = float(prix)
        i_qte = int(qte)
        if f_prix < 0 or i_qte < 0:
             return False, "Prix ou Quantité négatifs interdits"
    except ValueError:
        return False, "Prix ou Quantité doivent être numériques"

    df = load_products()
    if nom in df["Nom"].values:
        return False, "Produit existe déjà"

    cols = ["Nom", "Catégorie", "Prix", "Quantité"]
    new_row = pd.DataFrame([[nom, cat, f_prix, i_qte]], columns=cols)
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)
    return True, "Produit ajouté"


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
