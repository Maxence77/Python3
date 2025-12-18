"""
Interface en ligne de commande (CLI) pour l'application de gestion.
Point d'entrée principal pour l'utilisateur final.
"""

import os
import sys
import getpass
import pandas as pd
# Imports locaux
import products
import auth
import orders

# Configuration pour l'affichage Pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)


def clear_screen():
    """Efface l'écran du terminal pour une meilleure lisibilité."""
    os.system('cls' if os.name == 'nt' else 'clear') # nosec


def create_account_interaction():
    """Gère le formulaire de création de compte."""
    print("\n➕ --- CRÉATION DE COMPTE ---")
    new_user = input("Nouvel Identifiant : ").strip()
    new_pass = getpass.getpass("Nouveau Mot de passe : ").strip()

    if not new_user or not new_pass:
        print("❌ Erreur : Champs vides.")
        return

    # Appel à auth.py qui gère le sel, le hachage et l'API Pwned
    # Retourne soit "EXIST", soit un entier (nombre de fuites)
    status_or_count = auth.create_user(new_user, new_pass)

    if status_or_count == "EXIST":
        print("❌ Ce nom d'utilisateur est déjà pris.")
    else:
        print("✅ Compte créé avec succès !")
        # Si c'est un entier > 0, c'est que le mot de passe est compromis
        if isinstance(status_or_count, int) and status_or_count > 0:
            print(f"⚠️ ATTENTION : Mot de passe vu {status_or_count} fois dans des fuites.")
            print("   Nous vous conseillons fortement de le changer.")
        input("\nAppuyez sur Entrée pour revenir à la connexion...")


def login_step():
    """Gère la boucle de connexion ou d'inscription."""
    while True:
        clear_screen()
        print("==================================")
        print(" 🔐 AUTHENTIFICATION GROUPE3 ")
        print("==================================")
        print("Connectez-vous ou tapez 'C' pour Créer un compte.")
        print("Tapez 'Q' pour Quitter.")
        print("----------------------------------")

        user_input = input("Identifiant (ou C/Q) : ").strip()

        if user_input.lower() == 'q':
            print("Fermeture de l'application.")
            sys.exit()

        if user_input.lower() == 'c':
            create_account_interaction()
            continue

        # Tentative de connexion
        pwd = getpass.getpass("Mot de passe : ")
        status = auth.check_login(user_input, pwd)

        if status == "OK":
            print("✅ Connexion réussie !")
            return user_input

        if status == "COMPROMISED":
            print("⚠️ ALERTE : Connexion réussie, mais votre mot de passe est COMPROMIS !")
            print("   Veuillez le changer dès que possible.")
            input("Appuyez sur Entrée pour continuer...")
            return user_input

        print("❌ Identifiant ou mot de passe incorrect.")
        input("Appuyez sur Entrée pour réessayer...")


def display_menu(username):
    """Affiche le menu principal et retourne le choix de l'utilisateur."""
    print(f"\n👤 Utilisateur : {username}")
    print("==================================")
    print(" GESTION D'INVENTAIRE 🛡️")
    print("==================================")
    print("1. Afficher l'inventaire")
    print("2. Ajouter un produit")
    print("3. Rechercher un produit")
    print("4. Statistiques & Commandes")
    print("5. Administration (Users)")
    print("0. Quitter")
    return input("Votre choix : ")


def show_inventory():
    """Affiche la liste complète des produits."""
    df_prods = products.load_products()
    if df_prods.empty:
        print("\n📭 L'inventaire est vide.")
    else:
        print("\n📦 --- INVENTAIRE ACTUEL ---")
        # On remplace les NaN par vide pour l'affichage propre
        print(df_prods[["Nom", "Catégorie", "Prix", "Quantité"]].fillna("").to_string(index=False))


def add_product_interaction():
    """Interface pour ajouter un produit."""
    print("\n➕ --- AJOUT PRODUIT ---")
    nom = input("Nom : ").strip()
    cat = input("Catégorie (Info, Meuble, Vêtement...) : ").strip()
    try:
        prix_str = input("Prix : ")
        qty_str = input("Quantité : ")

        if not prix_str or not qty_str:
            print("❌ Erreur : Valeurs manquantes.")
            return

        prix = float(prix_str)
        qty = int(qty_str)

        if products.add_product(nom, cat, prix, qty):
            print("✅ Produit ajouté avec succès !")
        else:
            print("❌ Erreur : Ce produit existe déjà.")
    except ValueError:
        print("❌ Erreur : Veuillez entrer des nombres valides pour le prix et la quantité.")


def search_product_interaction():
    """Interface de recherche de produit."""
    query = input("\n🔍 Rechercher (Nom) : ").lower().strip()
    df_prods = products.load_products()

    if df_prods.empty:
        print("Inventaire vide.")
        return

    # Conversion en string pour éviter les erreurs si la colonne contient des nombres
    df_prods["Nom"] = df_prods["Nom"].astype(str)

    # Filtrage insensible à la casse
    results = df_prods[df_prods["Nom"].str.lower().str.contains(query, na=False)]

    if not results.empty:
        print(f"\n--- {len(results)} RÉSULTAT(S) ---")
        print(results[["Nom", "Catégorie", "Prix", "Quantité"]].to_string(index=False))
    else:
        print("Aucun produit trouvé.")


def stats_menu():
    """Affiche les KPI (Indicateurs clés de performance)."""
    print("\n📊 --- STATISTIQUES ---")
    df_prods = products.load_products()
    df_orders = orders.load_orders()

    # Calcul Valeur Stock : On force la conversion en numérique pour éviter les bugs
    stock_val = (
        pd.to_numeric(df_prods["Prix"], errors='coerce').fillna(0) *
        pd.to_numeric(df_prods["Quantité"], errors='coerce').fillna(0)
    ).sum()

    # Calcul CA
    if not df_orders.empty:
        ca_total = pd.to_numeric(df_orders["Prix Total"], errors='coerce').fillna(0).sum()
    else:
        ca_total = 0

    print(f"💰 Valeur du Stock : {stock_val:,.2f} €")
    print(f"📈 Chiffre d'Affaires : {ca_total:,.2f} €")
    print(f"🛒 Nombre de ventes : {len(df_orders)}")


def admin_menu():
    """Menu réservé à l'administrateur pour gérer les utilisateurs."""
    print("\n🔧 --- ADMINISTRATION ---")
    df_users = auth.load_users()
    print(df_users[["Username", "Compromised"]].to_string(index=False))

    choice = input("\n[S]upprimer un user ou [R]etour ? ").lower().strip()
    if choice == 's':
        target_user = input("Nom de l'utilisateur à supprimer : ").strip()
        auth.delete_user(target_user)
        print(f"Utilisateur '{target_user}' supprimé (s'il existait).")


def run_application():
    """Fonction principale de l'application."""
    # 1. Connexion
    current_user = login_step()

    # 2. Boucle du menu
    while True:
        choice = display_menu(current_user)

        if choice == '1':
            show_inventory()
        elif choice == '2':
            add_product_interaction()
        elif choice == '3':
            search_product_interaction()
        elif choice == '4':
            stats_menu()
        elif choice == '5':
            if current_user == "admin":
                admin_menu()
            else:
                print("⛔ Accès refusé. Réservé à l'administrateur.")
        elif choice == '0':
            print("Au revoir !")
            break
        else:
            print("❌ Choix invalide.")

        input("\nAppuyez sur Entrée pour continuer...")
        clear_screen()


if __name__ == "__main__":
    run_application()
