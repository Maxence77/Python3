import os
import time
import getpass
import pandas as pd

# Imports locaux
import auth
import products
import orders

class CLIApp:
    def __init__(self):
        self.current_user = None
        self.is_admin = False
        self.running = True

    def clear(self):
        """Nettoie la console (Windows ou Linux/Mac)."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def header(self, title="ACCUEIL"):
        self.clear()
        print("="*50)
        print(f"   ERP GROUPE 3 - CLI MODE [{title}]")
        if self.current_user:
            role = "ADMIN" if self.is_admin else "USER"
            print(f"   👤 Connecté: {self.current_user} ({role})")
        print("="*50)
        print("")

    def pause(self):
        input("\nAppuyez sur Entrée pour continuer...")

    # ==========================
    # BOUCLE PRINCIPALE & LOGIN
    # ==========================
    def run(self):
        while self.running:
            if not self.current_user:
                self.menu_login()
            else:
                self.menu_main()

    def menu_login(self):
        self.clear()
        print("=== ERP SYSTEM : CONNEXION ===")
        print("1. Se connecter")
        print("2. Créer un compte")
        print("3. Quitter")
        
        choice = input("\nChoix > ")

        if choice == "1":
            u = input("Utilisateur : ")
            p = getpass.getpass("Mot de passe : ") # Masque la saisie
            
            # Gestion des 3 statuts retournés par auth.py
            status, is_admin, _ = auth.authenticate_user(u, p)
            
            if status in ["SUCCESS", "WARNING"]:
                self.current_user = u
                self.is_admin = is_admin
                
                if status == "WARNING":
                    print("\n⚠️  ALERTE SÉCURITÉ ⚠️")
                    print("Votre mot de passe a été trouvé dans une fuite de données (API Pwned).")
                    print("Veuillez le changer immédiatement dans le menu Profil !")
                    self.pause()
                
                # Vérification des messages admin
                msgs = auth.get_user_messages(u)
                if msgs:
                    print("\n📬 VOUS AVEZ DES MESSAGES ADMIN :")
                    for m in msgs: print(f" - {m}")
                    self.pause()
            else:
                print("\n❌ Login incorrect.")
                self.pause()

        elif choice == "2":
            u = input("Nouvel utilisateur : ")
            p = getpass.getpass("Nouveau mot de passe : ")
            code, msg = auth.create_user(u, p)
            print(f"\nResultat : {msg}")
            self.pause()

        elif choice == "3":
            print("Au revoir.")
            self.running = False

    # ==========================
    # MENU PRINCIPAL
    # ==========================
    def menu_main(self):
        self.header("MENU PRINCIPAL")
        print("1. 📊 Dashboard")
        print("2. 📦 Commandes")
        print("3. 🏷️  Produits")
        print("4. 👤 Profil (Changer MDP)")
        
        if self.is_admin:
            print("5. 🛡️  ADMINISTRATION")
            print("0. Déconnexion")
        else:
            print("0. Déconnexion")

        choice = input("\nChoix > ")

        if choice == "1": self.view_dashboard()
        elif choice == "2": self.view_orders()
        elif choice == "3": self.view_products()
        elif choice == "4": self.view_profile()
        elif choice == "5" and self.is_admin: self.view_admin()
        elif choice == "0": self.current_user = None
        else: pass

    # ==========================
    # 1. DASHBOARD
    # ==========================
    def view_dashboard(self):
        self.header("DASHBOARD")
        df = orders.load_orders()
        
        if df.empty:
            print("Aucune donnée disponible.")
        else:
            # KPI
            ca = df["Prix Total"].sum()
            print(f"💰 CHIFFRE D'AFFAIRES TOTAL : {ca:.2f} €")
            print("-" * 30)
            
            # Top Produits (Mode texte)
            print("🏆 TOP 5 PRODUITS (par quantité) :")
            top = df.groupby("Produit")["Quantité"].sum().sort_values(ascending=False).head(5)
            print(top.to_string())
            print("-" * 30)

            # Dernières ventes
            print("📅 5 DERNIÈRES VENTES :")
            print(df[["Date", "Produit", "Prix Total"]].tail(5).to_string(index=False))

        self.pause()

    # ==========================
    # 2. COMMANDES
    # ==========================
    def view_orders(self):
        while True:
            self.header("GESTION COMMANDES")
            df = orders.load_orders()
            if not df.empty:
                # Affichage tableau simple
                print(f"{'ID':<5} {'Date':<12} {'Produit':<20} {'Qté':<5} {'Total':<10} {'Client'}")
                print("-" * 70)
                for _, r in df.iloc[::-1].iterrows(): # Ordre inverse
                    print(f"{r['ID']:<5} {r['Date']:<12} {r['Produit']:<20} {r['Quantité']:<5} {r['Prix Total']:<10} {r.get('Client','?')}")
            else:
                print("Pas de commandes.")

            print("\nACTIONS :")
            print("1. + Nouvelle Commande")
            print("2. ✏️  Modifier une commande")
            print("0. Retour")

            c = input("\nChoix > ")
            if c == "0": break
            elif c == "1": self.action_add_order()
            elif c == "2": self.action_edit_order()

    def action_add_order(self):
        print("\n--- NOUVELLE COMMANDE ---")
        # Liste produits dispos
        df_p = products.load_products()
        print("Produits : " + ", ".join(df_p["Nom"].tolist()))
        
        prod = input("Nom du produit : ")
        qty = input("Quantité : ")
        
        ok, msg = orders.create_order(self.current_user, prod, qty)
        print(f" > {msg}")
        time.sleep(1.5)

    def action_edit_order(self):
        oid = input("ID de la commande à modifier : ")
        if not oid: return
        
        # Liste produits dispos
        df_p = products.load_products()
        print("Produits dispos : " + ", ".join(df_p["Nom"].tolist()))

        prod = input("Nouveau produit : ")
        qty = input("Nouvelle quantité : ")
        
        ok, msg = orders.update_order(int(oid), prod, qty)
        print(f" > {msg}")
        time.sleep(1.5)

    # ==========================
    # 3. PRODUITS
    # ==========================
    def view_products(self):
        while True:
            self.header("GESTION PRODUITS")
            df = products.load_products()
            
            # Affichage
            print(f"{'Nom':<20} {'Catégorie':<15} {'Prix':<10} {'Stock'}")
            print("-" * 60)
            for _, r in df.iterrows():
                print(f"{r['Nom']:<20} {r['Catégorie']:<15} {r['Prix']:<10} {r['Quantité']}")

            print("\nACTIONS :")
            print("1. Ajouter Produit")
            print("2. Modifier Produit")
            print("3. Supprimer Produit")
            print("0. Retour")

            c = input("\nChoix > ")
            if c == "0": break
            elif c == "1":
                n = input("Nom : "); cat = input("Catégorie : ")
                p = float(input("Prix : ")); q = int(input("Stock : "))
                products.add_product(n, cat, p, q)
                print(" > Produit ajouté.")
                time.sleep(1)
            elif c == "2":
                old = input("Nom exact du produit à modifier : ")
                print("--- Nouvelles infos ---")
                n = input("Nouveau Nom : "); cat = input("Cat : ")
                p = float(input("Prix : ")); q = int(input("Stock : "))
                ok, msg = products.update_product_full(old, n, cat, p, q)
                print(f" > {msg}")
                time.sleep(1.5)
            elif c == "3":
                n = input("Nom du produit à supprimer : ")
                products.delete_product(n)
                print(" > Supprimé.")
                time.sleep(1)

    # ==========================
    # 4. PROFIL
    # ==========================
    def view_profile(self):
        self.header("MON PROFIL")
        print("Pour changer de mot de passe :")
        new_p = getpass.getpass("Nouveau mot de passe : ")
        confirm_p = getpass.getpass("Confirmer le mot de passe : ")
        
        if new_p != confirm_p:
            print("\n❌ Les mots de passe ne correspondent pas.")
        elif not new_p:
            print("\n❌ Annulé.")
        else:
            status, msg = auth.change_password(self.current_user, new_p)
            print(f"\n> {msg}")
        
        self.pause()

    # ==========================
    # 5. ADMIN
    # ==========================
    def view_admin(self):
        while True:
            self.header("ADMINISTRATION")
            df = auth.load_users()
            
            print(f"{'Username':<20} {'Admin':<10} {'Compromis?'}")
            print("-" * 50)
            for _, r in df.iterrows():
                is_adm = str(r['Admin']).lower() in ['true', '1', 'yes']
                adm_str = "OUI 👑" if is_adm else "NON"
                print(f"{r['Username']:<20} {adm_str:<10} {r['Compromised']}")

            print("\nACTIONS :")
            print("1. Changer rôle (Admin/User)")
            print("2. Supprimer utilisateur")
            print("3. Envoyer un message")
            print("0. Retour")

            c = input("\nChoix > ")
            if c == "0": break
            
            elif c == "1":
                u = input("Username : ")
                ok, msg = auth.toggle_admin_status(u)
                print(f" > {msg}")
                time.sleep(1.5)
                
            elif c == "2":
                u = input("Username à supprimer : ")
                if u == "admin": print(" > Impossible de supprimer le Super Admin.")
                else:
                    auth.delete_user(u)
                    print(" > Utilisateur supprimé.")
                time.sleep(1.5)
                
            elif c == "3":
                u = input("Destinataire : ")
                m = input("Message : ")
                auth.send_message(u, m)
                print(" > Message envoyé.")
                time.sleep(1)

if __name__ == "__main__":
    app = CLIApp()
    app.run()