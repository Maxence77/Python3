"""
Module de gestion des commandes pour l'ERP.
Gère la création, le chargement et la modification des commandes dans un fichier CSV.
"""

import datetime
import os

import pandas as pd
import products  # Import local pour la gestion des stocks et prix

ORDER_FILE = "csv/orders.csv"


def init_order_file():
    """Vérifie l'existence du dossier csv et initialise le fichier des commandes si nécessaire."""
    if not os.path.exists("csv"):
        os.makedirs("csv")
    if not os.path.exists(ORDER_FILE):
        df = pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité", "Prix Total", "Client"])
        df.to_csv(ORDER_FILE, index=False)


def load_orders():
    """Charge les commandes depuis le fichier CSV ou retourne un DataFrame vide en cas d'erreur."""
    init_order_file()
    try:
        return pd.read_csv(ORDER_FILE)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité", "Prix Total", "Client"])


def create_order(client, produit_nom, quantite):
    """Crée une nouvelle commande, met à jour le stock et calcule le prix total."""
    init_order_file()
    try:
        qty = int(quantite)
    except ValueError:
        return False, "Quantité invalide"

    # Vérification stock via products.py
    df_prod = products.load_products()
    prod_row = df_prod[df_prod["Nom"] == produit_nom]

    if prod_row.empty:
        return False, "Produit inconnu"

    stock_actuel = int(prod_row.iloc[0]["Quantité"])
    prix_unit = float(prod_row.iloc[0]["Prix"])

    if stock_actuel < qty:
        return False, f"Stock insuffisant ({stock_actuel} disp.)"

    # Mise à jour du stock
    products.update_product(
        produit_nom,
        produit_nom,
        prod_row.iloc[0]["Catégorie"],
        prix_unit,
        stock_actuel - qty
    )

    # Création commande
    df_orders = load_orders()
    new_id = 1 if df_orders.empty else int(df_orders["ID"].max()) + 1
    date_jour = datetime.datetime.now().strftime("%d/%m/%Y")
    total = prix_unit * qty

    new_row = pd.DataFrame(
        [[new_id, date_jour, produit_nom, qty, total, client]],
        columns=["ID", "Date", "Produit", "Quantité", "Prix Total", "Client"]
    )

    df_orders = pd.concat([df_orders, new_row], ignore_index=True)
    df_orders.to_csv(ORDER_FILE, index=False)
    return True, "Commande créée"


def update_order(order_id, new_prod, new_qty):
    """Modifie une commande existante et recalcule le prix total sans modifier le stock."""
    df_orders = load_orders()

    # On s'assure que l'ID est un entier pour la comparaison
    df_orders["ID"] = df_orders["ID"].astype(int)
    idx_list = df_orders.index[df_orders["ID"] == int(order_id)].tolist()

    if not idx_list:
        return False, "Commande introuvable"

    idx = idx_list[0]

    # Recalcul du prix basé sur les infos du produit
    df_prod = products.load_products()
    prod_row = df_prod[df_prod["Nom"] == new_prod]
    if prod_row.empty:
        return False, "Produit inconnu"

    try:
        qty = int(new_qty)
        p_unit = float(prod_row.iloc[0]["Prix"])
        total = qty * p_unit
    except ValueError:
        return False, "Erreur lors du calcul du prix"

    # Mise à jour des données dans le DataFrame
    df_orders.at[idx, "Produit"] = new_prod
    df_orders.at[idx, "Quantité"] = qty
    df_orders.at[idx, "Prix Total"] = total

    df_orders.to_csv(ORDER_FILE, index=False)
    return True, "Commande modifiée"
