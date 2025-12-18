"""
Module de calcul des statistiques (KPI).
Agrège les données des produits et des commandes pour le dashboard.
"""

import products
import orders


def get_global_stats():
    """
    Calcule les indicateurs clés de performance (KPI).
    Retourne un dictionnaire avec les totaux et moyennes.
    """
    # 1. Chargement des données
    df_prods = products.load_products()
    df_orders = orders.load_orders()

    # 2. Calculs sur les PRODUITS
    nb_produits = len(df_prods)
    valeur_stock = 0.0

    if not df_prods.empty:
        # On convertit en float/int pour sécuriser le calcul vectoriel
        valeur_stock = (
            df_prods["Prix"].astype(float) * df_prods["Quantité"].astype(int)
        ).sum()

    # 3. Calculs sur les COMMANDES
    nb_commandes = len(df_orders)
    chiffre_affaires = 0.0
    panier_moyen = 0.0

    if nb_commandes > 0 and not df_orders.empty:
        chiffre_affaires = df_orders["Prix Total"].astype(float).sum()
        panier_moyen = chiffre_affaires / nb_commandes

    # 4. On retourne un dictionnaire formaté
    return {
        "produits_count": int(nb_produits),
        "stock_valorisation": round(float(valeur_stock), 2),
        "commandes_count": int(nb_commandes),
        "chiffre_affaires": round(float(chiffre_affaires), 2),
        "panier_moyen": round(float(panier_moyen), 2)
    }
