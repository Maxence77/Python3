# inventory_manager.py
import csv

class InventoryManager:
    """
    Gère les opérations de l'inventaire des produits à partir d'un fichier CSV.
    Couvre la lecture de fichiers, l'ajout, le tri et la recherche. [cite: 14]
    """
    def __init__(self, filename="products.csv"):
        self.filename = filename
        self.products = self._load_products()

    def _load_products(self):
        """Charge les produits depuis le fichier CSV."""
        products = []
        try:
            with open(self.filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    products.append(row)
        except FileNotFoundError:
            print(f"Le fichier {self.filename} n'existe pas. Création d'un nouvel inventaire.")
        return products

    def _save_products(self):
        """Sauvegarde l'inventaire dans le fichier CSV."""
        if not self.products:
            return

        # Assurez-vous d'avoir les noms de colonnes (headers)
        fieldnames = self.products[0].keys()

        with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.products)

    def add_product(self, product_data):
        """Ajoute un nouveau produit."""
        # Exemple de product_data : {'name': 'Laptop', 'price': '1200.00', 'qty': '10'}
        self.products.append(product_data)
        self._save_products()
        print(f"Produit '{product_data.get('name', 'Inconnu')}' ajouté.")

    def display_products(self):
        """Affiche la liste actuelle des produits."""
        if not self.products:
            print("L'inventaire est vide.")
            return

        print("\n--- INVENTAIRE ---")
        for i, product in enumerate(self.products):
            print(f"ID: {i+1} | Nom: {product.get('name')} | Prix: {product.get('price')} | Qté: {product.get('qty')}")
        print("------------------")

    def search_product(self, query):
        """Recherche un produit par nom (insensible à la casse)."""
        results = [
            p for p in self.products
            if query.lower() in p.get('name', '').lower()
        ]
        return results

    def sort_products(self, key='name', reverse=False):
        """Trie les produits par une clé spécifiée."""
        # On utilise une fonction lambda pour gérer les conversions de type pour le tri
        # Ex: float(x['price']) pour le tri par prix
        try:
            sorted_list = sorted(
                self.products,
                key=lambda x: float(x[key]) if key in ['price', 'qty'] else x[key],
                reverse=reverse
            )
            self.products = sorted_list # Mise à jour de la liste triée
            self._save_products()
            print(f"Inventaire trié par '{key}'.")
        except KeyError:
            print(f"Clé de tri '{key}' non valide.")
        except ValueError:
            print("Erreur de conversion de type lors du tri (vérifiez les données).")