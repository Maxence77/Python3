import pandas as pd
import os
import products

CSV_FOLDER = "csv"
ORDERS_FILE = os.path.join(CSV_FOLDER, "orders.csv")

if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        # Structure de la commande
        df = pd.DataFrame(columns=["ID", "Client", "Produit", "Quantité", "Prix Total", "Date"])
        df.to_csv(ORDERS_FILE, index=False)
        return df
    return pd.read_csv(ORDERS_FILE)

def create_order(client, nom_produit, quantite):
    """
    CRUD Create avec Validation Stock (Module 5A)
    """
    df_prods = products.load_products()
    product_row = df_prods[df_prods["Nom"] == nom_produit]
    
    if product_row.empty:
        return "Produit introuvable"
    
    stock_dispo = int(product_row.iloc[0]["Quantité"])
    prix_unitaire = float(product_row.iloc[0]["Prix"])
    
    # 1. Validation des données
    try:
        quantite = int(quantite)
        if quantite <= 0:
            return "La quantité doit être positive."
    except:
        return "Format quantité invalide."

    # 2. Vérification Stock
    if quantite > stock_dispo:
        return f"Stock insuffisant (Dispo: {stock_dispo})"

    # 3. Création Commande
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
    
    # 4. Mise à jour Stock (Décrément)
    products.update_stock(nom_produit, quantite)
    
    # 5. Sauvegarde
    df_orders = pd.concat([df_orders, new_order], ignore_index=True)
    df_orders.to_csv(ORDERS_FILE, index=False)
    
    return "OK"