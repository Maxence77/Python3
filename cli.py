import os
import getpass
import pandas as pd

import products
import auth
import orders

# Configuration pour l'affichage Pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def create_account_interaction():
    """Gère la création de compte depuis le CLI."""
    print("\n➕ --- CRÉATION DE COMPTE ---")
    new_user = input("Nouvel Identifiant : ")
    new_pass = getpass.getpass("Nouveau Mot de passe : ")
    
    if not new_user or not new_pass:
        print("❌ Erreur : Champs vides.")
        return

    # Il gère le sel, le hachage et l'API 
    res = auth.create_user(new_user, new_pass)
    
    if res == "EXIST":
        print("❌ Ce nom d'utilisateur est déjà pris.")
    else:
        # contient le nombre de fois où le mdp a été vu dans des fuites
        print("✅ Compte créé avec succès !")
        if res > 0:
            print(f"⚠️ ATTENTION : Ce mot de passe est apparu {res} fois dans des fuites de données.")
            print("   Nous vous conseillons fortement de le changer.")
        input("\nAppuyez sur Entrée pour revenir à la connexion...")

def login_step():
    """Étape de connexion ou d'inscription."""
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
            print("Fermeture.")
            exit()
            
        if user_input.lower() == 'c':
            create_account_interaction()
            continue # On recommence la boucle pour se connecter après création

        # Si ce n'est pas C ou Q, on tente le login
        pwd = getpass.getpass("Mot de passe : ")
        
        status = auth.check_login(user_input, pwd)
        
        if status == "OK":
            print("✅ Connexion réussie !")
            return user_input
        elif status == "COMPROMISED":
            print("⚠️ ALERTE : Connexion réussie, mais votre mot de passe est COMPROMIS !")
            print("   Veuillez le changer dès que possible.")
            input("Appuyez sur Entrée pour continuer...")
            return user_input
        else:
            print("❌ Identifiant ou mot de passe incorrect.")
            input("Appuyez sur Entrée pour réessayer...")

def display_menu(username):
    """Affiche le menu principal."""
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
    df = products.load_products()
    if df.empty:
        print("\n📭 L'inventaire est vide.")
    else:
        print("\n📦 --- INVENTAIRE ACTUEL ---")
        print(df[["Nom", "Catégorie", "Prix", "Quantité"]].to_string(index=False))

def add_product_interaction():
    print("\n➕ --- AJOUT PRODUIT ---")
    nom = input("Nom : ")
    cat = input("Catégorie (Info, Meuble, Vêtement...) : ")
    try:
        prix = float(input("Prix : "))
        qty = int(input("Quantité : "))
        
        if products.add_product(nom, cat, prix, qty):
            print("✅ Produit ajouté avec succès !")
        else:
            print("❌ Erreur : Ce produit existe déjà.")
    except ValueError:
        print("❌ Erreur : Veuillez entrer des nombres valides.")

def search_product_interaction():
    query = input("\n🔍 Rechercher (Nom) : ").lower()
    df = products.load_products()
    
    # Filtrage Pandas
    results = df[df["Nom"].str.lower().str.contains(query, na=False)]
    
    if not results.empty:
        print(f"\n--- {len(results)} RÉSULTAT(S) ---")
        print(results[["Nom", "Catégorie", "Prix", "Quantité"]].to_string(index=False))
    else:
        print("Aucun produit trouvé.")

def stats_menu():
    print("\n📊 --- STATISTIQUES ---")
    df_prods = products.load_products()
    df_orders = orders.load_orders()
    
    valeur_stock = (df_prods["Prix"] * df_prods["Quantité"]).sum()
    ca = df_orders["Prix Total"].sum() if not df_orders.empty else 0
    
    print(f"💰 Valeur du Stock : {valeur_stock:,.2f} €")
    print(f"📈 Chiffre d'Affaires : {ca:,.2f} €")
    print(f"🛒 Nombre de ventes : {len(df_orders)}")

def admin_menu():
    print("\n🔧 --- ADMINISTRATION ---")
    df_users = auth.load_users()
    print(df_users[["Username", "Compromised"]].to_string(index=False))
    
    choice = input("\n[S]upprimer un user ou [R]etour ? ").lower()
    if choice == 's':
        u = input("Nom de l'utilisateur à supprimer : ")
        auth.delete_user(u)
        print("Action effectuée.")

def run_application():
    # 1. Connexion ou Création de compte
    current_user = login_step()
    
    # 2. Boucle principale
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
                print("⛔ Hop hop hop accès refusé. Réservé à l'admin.")
        elif choice == '0':
            print("Au revoir !")
            break
        else:
            print("Choix invalide.")
        
        input("\nAppuyez sur Entrée pour continuer...")
        clear_screen()

if __name__ == "__main__":
    run_application()