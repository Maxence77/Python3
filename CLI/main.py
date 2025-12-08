# main.py
from inventory_manager import InventoryManager
from auth import check_pwned_password

# Initialisation des gestionnaires
inventory_mgr = InventoryManager("products.csv")

def display_menu():
    """Affiche le menu de l'application."""
    print("\n==================================")
    print(" GESTION D'INVENTAIRE SÉCURISÉE 🛡️")
    print("==================================")
    print("1. Afficher l'inventaire")
    print("2. Ajouter un produit")
    print("3. Rechercher un produit")
    print("4. Trier l'inventaire")
    print("5. **Vérifier la sécurité d'un mot de passe**")
    print("0. Quitter")
    choice = input("Veuillez entrer votre choix : ")
    return choice

def run_application():
    """Fonction principale de l'application."""
    while True:
        choice = display_menu()

        if choice == '1':
            inventory_mgr.display_products()

        elif choice == '2':
            # Collecte des données pour l'ajout
            name = input("Nom du produit : ")
            while True:
                try:
                    price = float(input("Prix : "))
                    qty = int(input("Quantité : "))
                    break
                except ValueError:
                    print("Veuillez entrer des nombres valides pour le prix et la quantité.")
            
            product = {'name': name, 'price': str(price), 'qty': str(qty)}
            inventory_mgr.add_product(product)

        elif choice == '3':
            query = input("Entrez le nom ou une partie du nom du produit à rechercher : ")
            results = inventory_mgr.search_product(query)
            if results:
                print(f"\n--- {len(results)} RÉSULTAT(S) TROUVÉ(S) ---")
                for product in results:
                    print(f"Nom: {product.get('name')} | Prix: {product.get('price')} | Qté: {product.get('qty')}")
            else:
                print("Aucun produit trouvé.")

        elif choice == '4':
            key = input("Trier par (name, price, qty) : ").lower()
            reverse_str = input("Tri descendant ? (o/n) : ").lower()
            reverse = reverse_str == 'o'
            inventory_mgr.sort_products(key=key, reverse=reverse)

        elif choice == '5':
            # Jalon 4 - Détection des compromis via API [cite: 15]
            password = input("Entrez le mot de passe à vérifier (ne sera pas stocké) : ")
            count = check_pwned_password(password)
            
            if count > 0:
                print(f"🚨 DANGER! Ce mot de passe a été compromis {count} fois dans des fuites de données connues.")
            elif count == 0:
                print("✅ Bonne nouvelle! Ce mot de passe n'apparaît pas dans les fuites de données connues.")
            elif count == -1:
                print("⚠️ Impossible de vérifier la compromission. Erreur de connexion API.")

        elif choice == '0':
            print("Merci d'avoir utilisé l'application. Au revoir!")
            break

        else:
            print("Choix non valide. Veuillez réessayer.")

if __name__ == "__main__":
    run_application()