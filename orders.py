import pandas as pd
import os
import datetime
import products  # On a besoin de products pour recalculer le prix

ORDER_FILE = "csv/orders.csv"

def init_order_file():
    if not os.path.exists("csv"): os.makedirs("csv")
    if not os.path.exists(ORDER_FILE):
        df = pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité", "Prix Total", "Client"])
        df.to_csv(ORDER_FILE, index=False)

def load_orders():
    init_order_file()
    try:
        return pd.read_csv(ORDER_FILE)
    except:
        return pd.DataFrame(columns=["ID", "Date", "Produit", "Quantité", "Prix Total", "Client"])

def create_order(client, produit_nom, quantite):
    init_order_file()
    try:
        qty = int(quantite)
    except:
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
    products.update_product(produit_nom, produit_nom, prod_row.iloc[0]["Catégorie"], prix_unit, stock_actuel - qty)

    # Création commande
    df_orders = load_orders()
    new_id = 1 if df_orders.empty else df_orders["ID"].max() + 1
    date_jour = datetime.datetime.now().strftime("%d/%m/%Y")
    total = prix_unit * qty

    new_row = pd.DataFrame([[new_id, date_jour, produit_nom, qty, total, client]], 
                           columns=["ID", "Date", "Produit", "Quantité", "Prix Total", "Client"])
    
    df_orders = pd.concat([df_orders, new_row], ignore_index=True)
    df_orders.to_csv(ORDER_FILE, index=False)
    return True, "Commande créée"

# --- NOUVELLE FONCTION ---
def update_order(order_id, new_prod, new_qty):
    """Modifie une commande existante et recalcule le prix."""
    df = load_orders()
    
    # Trouver l'index de la commande
    # On convertit ID en int pour être sûr
    df["ID"] = df["ID"].astype(int)
    idx_list = df.index[df["ID"] == int(order_id)].tolist()
    
    if not idx_list:
        return False, "Commande introuvable"
    
    idx = idx_list[0]
    
    # Recalcul du prix
    df_prod = products.load_products()
    prod_row = df_prod[df_prod["Nom"] == new_prod]
    if prod_row.empty:
        return False, "Produit inconnu"
        
    try:
        q = int(new_qty)
        p_unit = float(prod_row.iloc[0]["Prix"])
        total = q * p_unit
    except:
        return False, "Erreur calcul prix"

    # Mise à jour (Note: Pour faire simple, on ne re-gère pas le stock ici pour l'instant
    # car c'est complexe de remettre l'ancien stock et enlever le nouveau. 
    # On change juste la commande).
    df.at[idx, "Produit"] = new_prod
    df.at[idx, "Quantité"] = q
    df.at[idx, "Prix Total"] = total
    
    df.to_csv(ORDER_FILE, index=False)
    return True, "Commande modifiée"