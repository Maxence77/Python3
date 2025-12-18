"""
Module de gestion des commandes (Create/Read).
Gère le fichier CSV des commandes et la validation des stocks.
"""
import os
import pandas as pd
import products

# --- CONFIGURATION ---
CSV_FOLDER = "csv"
ORDERS_FILE = os.path.join(CSV_FOLDER, "orders.csv")

if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)


def load_orders():
    """Charge le fichier CSV des commandes ou en crée un vide."""
    if not os.path.exists(ORDERS_FILE):
        df_orders = pd.DataFrame(columns=[
            "ID", "Client", "Produit", "Quantité", "Prix Total", "Date"
        ])
        df_orders.to_csv(ORDERS_FILE, index=False)
        return df_orders
    return pd.read_csv(ORDERS_FILE)


def create_order(client, nom_produit, quantite):
    """
    Crée une commande avec validation du stock.
    Retourne un tuple (Succès: bool, Message: str).
    """
    df_prods = products.load_products()
    # Recherche du produit
    product_row = df_prods[df_prods["Nom"] == nom_produit]
    if product_row.empty:
        return False, "Produit introuvable"
    # Récupération des infos produit
    record = product_row.iloc[0]
    stock_dispo = int(record["Quantité"])
    prix_unitaire = float(record["Prix"])
    categorie = record["Catégorie"]
    # 1. Validation des données (Conversion)
    try:
        quantite = int(quantite)
        if quantite <= 0:
            return False, "La quantité doit être positive."
    except ValueError:
        return False, "Format quantité invalide."
    # 2. Vérification Stock
    if quantite > stock_dispo:
        return False, f"Stock insuffisant (Dispo: {stock_dispo})"
    # 3. Création de la ligne Commande
    df_orders = load_orders()
    new_id = len(df_orders) + 1
    total = prix_unitaire * quantite
    new_order = pd.DataFrame([{
        "ID": new_id,
        "Client": client,
        "Produit": nom_produit,
        "Quantité": quantite,
        "Prix Total": total,
        "Date": pd.Timestamp.now().strftime('%Y-%m-%d')
    }])
    # 4. Mise à jour Stock (Décrémentation)
    # On utilise update_product car update_stock n'existe pas forcément
    new_stock = stock_dispo - quantite
    products.update_product(nom_produit, nom_produit, categorie, prix_unitaire, new_stock)
    # 5. Sauvegarde Commande
    df_orders = pd.concat([df_orders, new_order], ignore_index=True)
    df_orders.to_csv(ORDERS_FILE, index=False)
    return True, "Commande validée avec succès"
