"""
Module de gestion du stock produits (CRUD).
Gère le fichier CSV des produits, l'ajout, la modification,
la suppression et la mise à jour des quantités.
"""

import os
import pandas as pd

# --- CONFIGURATION ---
CSV_FOLDER = "csv"
PRODUCTS_FILE = os.path.join(CSV_FOLDER, "products.csv")

if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)


def load_products():
    """Charge le fichier CSV des produits ou en crée un vide."""
    if not os.path.exists(PRODUCTS_FILE):
        df_products = pd.DataFrame(columns=[
            "Nom", "Catégorie", "Prix", "Quantité", "Date Ajout"
        ])
        df_products.to_csv(PRODUCTS_FILE, index=False)
        return df_products
    return pd.read_csv(PRODUCTS_FILE)


def add_product(nom, categorie, prix, quantite):
    """Ajoute un nouveau produit s'il n'existe pas déjà."""
    df_products = load_products()

    # Vérification doublon (nettoyage des noms pour comparaison)
    if not df_products.empty:
        existing_names = df_products["Nom"].astype(str).str.strip().values
        if str(nom).strip() in existing_names:
            return False

    new_data = pd.DataFrame([{
        "Nom": str(nom).strip(),
        "Catégorie": categorie,
        "Prix": float(prix),
        "Quantité": int(quantite),
        "Date Ajout": pd.Timestamp.now().strftime('%Y-%m-%d')
    }])

    df_products = pd.concat([df_products, new_data], ignore_index=True)
    df_products.to_csv(PRODUCTS_FILE, index=False)
    return True


def update_product(old_name, new_name, new_cat, new_price, new_qty):
    """Met à jour les informations d'un produit existant."""
    df_products = load_products()

    # Recherche de l'index du produit
    idx = df_products.index[df_products["Nom"] == old_name].tolist()

    if idx:
        i = idx[0]
        df_products.at[i, "Nom"] = new_name
        df_products.at[i, "Catégorie"] = new_cat
        df_products.at[i, "Prix"] = float(new_price)
        df_products.at[i, "Quantité"] = int(new_qty)

        df_products.to_csv(PRODUCTS_FILE, index=False)
        return True
    return False


def delete_product(nom_produit):
    """Supprime un produit du stock."""
    df_products = load_products()

    if df_products.empty:
        return False

    # Nettoyage pour comparaison fiable
    df_products["Nom"] = df_products["Nom"].astype(str).str.strip()
    cible = str(nom_produit).strip()

    if cible in df_products["Nom"].values:
        # On garde tout ce qui n'est PAS la cible
        df_products = df_products[df_products["Nom"] != cible]
        df_products.to_csv(PRODUCTS_FILE, index=False)
        return True

    return False


def update_stock(nom_produit, qty_vendue):
    """
    Décrémente le stock d'un produit après une vente.
    Utilisé pour les mises à jour rapides de quantité.
    """
    df_products = load_products()
    idx = df_products.index[df_products["Nom"] == nom_produit].tolist()

    if idx:
        current_qty = df_products.at[idx[0], "Quantité"]
        df_products.at[idx[0], "Quantité"] = current_qty - qty_vendue
        df_products.to_csv(PRODUCTS_FILE, index=False)
        return True
    return False


def get_product(nom_produit):
    """Cherche un produit spécifique et retourne ses infos ou None."""
    df_products = load_products()

    if df_products.empty:
        return None

    # Nettoyage pour comparaison fiable
    df_products["Nom"] = df_products["Nom"].astype(str).str.strip()
    cible = str(nom_produit).strip()

    # Filtrage
    resultat = df_products[df_products["Nom"] == cible]

    if not resultat.empty:
        # On retourne la première ligne trouvée sous forme de dictionnaire
        return resultat.iloc[0].to_dict()

    return None
