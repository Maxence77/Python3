# inventory_manager.py
import csv

class InventoryManager:
    """
    Gère les opérations de l'inventaire des produits à partir d'un fichier CSV.
    Couvre la lecture de fichiers, l'ajout, le tri et la recherche.
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
            # On ne print pas dans le GUI, on laisse passer
            pass
        return products

    def _save_products(self):
        """Sauvegarde l'inventaire dans le fichier CSV."""
        if not self.products:
            return

        fieldnames = self.products[0].keys()

        with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.products)

    def add_product(self, product_data):
        """Ajoute un nouveau produit."""
        self.products.append(product_data)
        self._save_products()
        # Le print reste pour debug, mais le GUI donnera le feedback visuel
        print(f"Produit '{product_data.get('name', 'Inconnu')}' ajouté.")

    def display_products(self):
        """
        Dans le contexte GUI, cette fonction retourne la liste brute 
        au lieu de l'imprimer, pour que l'interface puisse l'afficher.
        """
        return self.products

    def search_product(self, query):
        """Recherche un produit par nom (insensible à la casse)."""
        results = [
            p for p in self.products
            if query.lower() in p.get('name', '').lower()
        ]
        return results

    def sort_products(self, key='name', reverse=False):
        """Trie les produits par une clé spécifiée."""
        try:
            sorted_list = sorted(
                self.products,
                key=lambda x: float(x[key]) if key in ['price', 'qty'] else x[key].lower(),
                reverse=reverse
            )
            self.products = sorted_list
            self._save_products()
        except (KeyError, ValueError):
            pass # Gestion d'erreur silencieuse pour le GUI