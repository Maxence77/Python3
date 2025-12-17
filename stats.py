import products
import orders
import pandas as pd

def get_global_stats():
    """
    Calcule les indicateurs clés de performance (KPI).
    """
    # 1. Chargement des données
    df_prods = products.load_products()
    df_orders = orders.load_orders()
    
    # 2. Calculs sur les PRODUITS
    nb_produits = len(df_prods)
    
    # Valeur du stock = Somme de (Prix * Quantité) pour chaque ligne
    # On convertit en float pour éviter les erreurs
    valeur_stock = (df_prods["Prix"].astype(float) * df_prods["Quantité"].astype(int)).sum()
    
    # 3. Calculs sur les COMMANDES
    nb_commandes = len(df_orders)
    
    if nb_commandes > 0:
        chiffre_affaires = df_orders["Prix Total"].astype(float).sum()
        panier_moyen = chiffre_affaires / nb_commandes
    else:
        chiffre_affaires = 0
        panier_moyen = 0

    # 4. On retourne un beau dictionnaire
    return {
        "produits_count": int(nb_produits),
        "stock_valorisation": round(float(valeur_stock), 2),
        "commandes_count": int(nb_commandes),
        "chiffre_affaires": round(float(chiffre_affaires), 2),
        "panier_moyen": round(float(panier_moyen), 2)
    }