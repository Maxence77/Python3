"""
Module d'interface en ligne de commande (CLI) pour l'ERP.
Gère les interactions utilisateur, les menus et l'affichage des données.
"""

import getpass
import os
import subprocess
import time

# Imports locaux
import auth
import products
import orders


class CLIApp:
    """
    Classe principale gérant l'application en mode console.
    """

    def __init__(self):
        """Initialise l'état de l'application."""
        self.current_user = None
        self.is_admin = False
        self.running = True

    def clear(self):
        """Nettoie la console (Windows ou Linux/Mac) de manière sécurisée."""
        if os.name == "nt":
            subprocess.run(
                ["cmd", "/c", "cls"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.run(
                ["clear"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

    def header(self, title="ACCUEIL"):
        """Affiche l'en-tête de l'application avec les infos utilisateur."""
        self.clear()
        print("=" * 50)
        print(f"   ERP GROUPE 3 - CLI MODE [{title}]")
        if self.current_user:
            role = "ADMIN" if self.is_admin else "USER"
            print(f"   👤 Connecté: {self.current_user} ({role})")
        print("=" * 50)
        print("")

    def pause(self):
        """Attend une action de l'utilisateur avant de continuer."""
        input("\nAppuyez sur Entrée pour continuer...")

    def run(self):
        """Boucle principale de l'application."""
        while self.running:
            if not self.current_user:
                self.menu_login()
            else:
                self.menu_main()

    def menu_login(self):
        """Gère l'écran de connexion et de création de compte."""
        self.clear()
        print("=== ERP SYSTEM : CONNEXION ===")
        print("1. Se connecter")
        print("2. Créer un compte")
        print("3. Quitter")

        choice = input("\nChoix > ")

        if choice == "1":
            user = input("Utilisateur : ")
            pwd = getpass.getpass("Mot de passe : ")
            status, is_admin, _ = auth.authenticate_user(user, pwd)

            if status in ["SUCCESS", "WARNING"]:
                self.current_user = user
                self.is_admin = is_admin
                if status == "WARNING":
                    print("\n⚠️  ALERTE SÉCURITÉ ⚠️")
                    print("Mot de passe trouvé dans une fuite de données.")
                    self.pause()

                msgs = auth.get_user_messages(user)
                if msgs:
                    print("\n📬 MESSAGES ADMIN :")
                    for msg in msgs:
                        print(f" - {msg}")
                    self.pause()
            else:
                print("\n❌ Login incorrect.")
                self.pause()

        elif choice == "2":
            user = input("Nouvel utilisateur : ")
            pwd = getpass.getpass("Nouveau mot de passe : ")
            _, msg = auth.create_user(user, pwd)
            print(f"\nResultat : {msg}")
            self.pause()

        elif choice == "3":
            print("Au revoir.")
            self.running = False

    def menu_main(self):
        """Affiche le menu principal après connexion."""
        self.header("MENU PRINCIPAL")
        print("1. 📊 Dashboard\n2. 📦 Commandes\n3. 🏷️  Produits")
        print("4. 👤 Profil")
        if self.is_admin:
            print("5. 🛡️  ADMINISTRATION")
        print("0. Déconnexion")

        choice = input("\nChoix > ")
        actions = {
            "1": self.view_dashboard,
            "2": self.view_orders,
            "3": self.view_products,
            "4": self.view_profile,
            "5": self.view_admin if self.is_admin else None,
            "0": self._logout
        }
        action = actions.get(choice)
        if action:
            action()

    def _logout(self):
        self.current_user = None

    def view_dashboard(self):
        """Affiche les statistiques clés de l'ERP."""
        self.header("DASHBOARD")
        df = orders.load_orders()
        if df.empty:
            print("Aucune donnée disponible.")
        else:
            ca_total = df["Prix Total"].sum()
            print(f"💰 CHIFFRE D'AFFAIRES TOTAL : {ca_total:.2f} €")
            print("-" * 30)
            print("🏆 TOP 5 PRODUITS (par quantité) :")
            top = df.groupby("Produit")["Quantité"].sum().sort_values(ascending=False).head(5)
            print(top.to_string())
        self.pause()

    def view_orders(self):
        """Menu de gestion des commandes."""
        while True:
            self.header("GESTION COMMANDES")
            df = orders.load_orders()
            if not df.empty:
                print(f"{'ID':<5} {'Date':<12} {'Produit':<20} {'Qté':<5} {'Total'}")
                print("-" * 60)
                for _, r in df.iloc[::-1].iterrows():
                    print(f"{r['ID']:<5} {r['Date']:<12} {r['Produit']:<20} "
                          f"{r['Quantité']:<5} {r['Prix Total']}")
            else:
                print("Pas de commandes.")

            print("\n1. + Nouvelle Commande\n2. ✏️  Modifier\n0. Retour")
            choice = input("\nChoix > ")
            if choice == "0":
                break
            if choice == "1":
                self.action_add_order()
            elif choice == "2":
                self.action_edit_order()

    def action_add_order(self):
        """Logique d'ajout d'une commande."""
        df_p = products.load_products()
        print("Produits : " + ", ".join(df_p["Nom"].tolist()))
        prod = input("Nom du produit : ")
        qty = input("Quantité : ")
        _, msg = orders.create_order(self.current_user, prod, qty)
        print(f" > {msg}")
        time.sleep(1.5)

    def action_edit_order(self):
        """Logique de modification d'une commande."""
        oid = input("ID de la commande à modifier : ")
        if not oid:
            return
        prod = input("Nouveau produit : ")
        qty = input("Nouvelle quantité : ")
        _, msg = orders.update_order(int(oid), prod, qty)
        print(f" > {msg}")
        time.sleep(1.5)

    def view_products(self):
        """Menu de gestion du catalogue produits."""
        while True:
            self.header("GESTION PRODUITS")
            df = products.load_products()
            print(f"{'Nom':<20} {'Catégorie':<15} {'Prix':<10} {'Stock'}")
            print("-" * 60)
            for _, r in df.iterrows():
                print(f"{r['Nom']:<20} {r['Catégorie']:<15} {r['Prix']:<10} {r['Quantité']}")

            print("\n1. Ajouter\n2. Modifier\n3. Supprimer\n0. Retour")
            choice = input("\nChoix > ")
            if choice == "0":
                break
            self._handle_product_action(choice)

    def _handle_product_action(self, choice):
        if choice == "1":
            n = input("Nom : ")
            cat = input("Catégorie : ")
            p = float(input("Prix : "))
            q = int(input("Stock : "))
            products.add_product(n, cat, p, q)
            print(" > Produit ajouté.")
        elif choice == "2":
            old = input("Nom du produit à modifier : ")
            n = input("Nouveau Nom : ")
            cat = input("Cat : ")
            p = float(input("Prix : "))
            q = int(input("Stock : "))
            # Correction de l'appel : update_product (pas update_product_full)
            products.update_product(old, n, cat, p, q)
            print(" > Produit mis à jour.")
        elif choice == "3":
            n = input("Nom du produit à supprimer : ")
            products.delete_product(n)
            print(" > Supprimé.")
        time.sleep(1)

    def view_profile(self):
        """Permet à l'utilisateur de modifier son mot de passe."""
        self.header("MON PROFIL")
        new_p = getpass.getpass("Nouveau mot de passe : ")
        confirm = getpass.getpass("Confirmer : ")
        if new_p != confirm:
            print("\n❌ Erreur de correspondance.")
        else:
            _, msg = auth.change_password(self.current_user, new_p)
            print(f"\n> {msg}")
        self.pause()

    def view_admin(self):
        """Menu réservé aux administrateurs."""
        while True:
            self.header("ADMINISTRATION")
            df = auth.load_users()
            print(f"{'Username':<20} {'Admin':<10} {'Compromis?'}")
            print("-" * 50)
            for _, r in df.iterrows():
                is_adm = str(r['Admin']).lower() in ['true', '1', 'yes']
                adm_str = "OUI 👑" if is_adm else "NON"
                print(f"{r['Username']:<20} {adm_str:<10} {r['Compromised']}")

            print("\n1. Changer rôle\n2. Supprimer\n3. Message\n0. Retour")
            c = input("\nChoix > ")
            if c == "0":
                break
            self._handle_admin_action(c)

    def _handle_admin_action(self, choice):
        if choice == "1":
            u = input("Username : ")
            _, msg = auth.toggle_admin_status(u)
            print(f" > {msg}")
        elif choice == "2":
            u = input("Username à supprimer : ")
            if u != "admin":
                auth.delete_user(u)
                print(" > Utilisateur supprimé.")
        elif choice == "3":
            u = input("Destinataire : ")
            m = input("Message : ")
            auth.send_message(u, m)
            print(" > Message envoyé.")
        time.sleep(1.5)


if __name__ == "__main__":
    app = CLIApp()
    app.run()
