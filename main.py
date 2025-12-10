import tkinter as tk
from tkinter import ttk, messagebox
from inventory_manager import InventoryManager
from auth import check_pwned_password, hash_password, verify_password

# --- CONFIGURATION UTILISATEUR (Simulation BDD) ---
# Pour cet exercice, on crée un utilisateur "admin" en dur.
# Dans un vrai projet, ceci viendrait d'un fichier users.csv ou d'une BDD.
ADMIN_LOGIN = "admin"
# On génère le hash de "admin123" pour simuler un stockage sécurisé
SALT_SIMUL, HASH_SIMUL = hash_password("admin123")
 
# --- VARIABLES GLOBALES ---
inventory_mgr = InventoryManager("products.csv")
root = None
main_frame = None # Contiendra soit le Login, soit le Dashboard et oui
# Variables widgets Dashboard
tree = None
entry_name = None
entry_price = None
entry_qty = None
entry_search = None

# --- FONCTIONS DU DASHBOARD (INVENTAIRE) ---

def refresh_tree(data=None):
    for item in tree.get_children():
        tree.delete(item)
    products = data if data is not None else inventory_mgr.display_products()
    for p in products:
        tree.insert('', tk.END, values=(p.get('name'), p.get('price'), p.get('qty')))

def action_add_product():
    name, price, qty = entry_name.get(), entry_price.get(), entry_qty.get()
    if not name or not price or not qty:
        messagebox.showwarning("Attention", "Champs vides.")
        return
    try:
        float(price); int(qty)
        inventory_mgr.add_product({'name': name, 'price': str(price), 'qty': str(qty)})
        entry_name.delete(0, tk.END); entry_price.delete(0, tk.END); entry_qty.delete(0, tk.END)
        refresh_tree()
        messagebox.showinfo("Succès", "Produit ajouté.")
    except ValueError:
        messagebox.showerror("Erreur", "Format invalide.")

def action_search_product():
    query = entry_search.get()
    refresh_tree(inventory_mgr.search_product(query))

def action_sort_products(key):
    inventory_mgr.sort_products(key=key)
    refresh_tree()

def logout():
    """Déconnecte l'utilisateur et revient au login."""
    display_login_screen()

# --- FONCTIONS DE GESTION D'INTERFACE (LOGIN vs DASHBOARD) ---

def clear_window():
    """Supprime tous les widgets de la fenêtre principale."""
    for widget in root.winfo_children():
        widget.destroy()

def attempt_login(username, password):
    """
    Gère la logique de connexion ET la vérification de sécurité (Jalon 4).
    """
    if not username or not password:
        messagebox.showwarning("Erreur", "Veuillez remplir tous les champs.")
        return

    # 1. Check Sécurité API (Jalon 4)
    # On vérifie si ce mot de passe traîne sur internet
    pwned_count = check_pwned_password(password)
    
    if pwned_count > 0:
        # On avertit l'utilisateur, mais on ne bloque pas forcément l'accès si c'est le bon MDP
        messagebox.showwarning(
            "SÉCURITÉ ALERTE 🚨", 
            f"Attention ! Ce mot de passe a été trouvé {pwned_count} fois dans des fuites de données publiques.\n\n"
            "Nous vous conseillons de le changer immédiatement."
        )
    elif pwned_count == -1:
        # Erreur silencieuse ou log
        print("Erreur connexion API HIBP")

    # 2. Vérification des identifiants (Local)
    if username == ADMIN_LOGIN and verify_password(SALT_SIMUL, HASH_SIMUL, password):
        messagebox.showinfo("Bienvenue", "Connexion réussie !")
        display_dashboard_screen()
    else:
        messagebox.showerror("Erreur", "Identifiant ou mot de passe incorrect.")

def display_dashboard_screen():
    """Construit l'interface de gestion (l'ancien menu)."""
    clear_window()
    
    # Configuration globale
    root.geometry("900x600")
    root.title("Gestion d'Inventaire - Connecté")

    # Header avec bouton Déconnexion
    header_frame = ttk.Frame(root)
    header_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(header_frame, text="TABLEAU DE BORD", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
    ttk.Button(header_frame, text="Se déconnecter", command=logout).pack(side=tk.RIGHT)

    # --- Zone Gauche : Ajout ---
    frame_left = ttk.LabelFrame(root, text="Ajouter un produit")
    frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    global entry_name, entry_price, entry_qty
    ttk.Label(frame_left, text="Nom :").pack(anchor=tk.W)
    entry_name = ttk.Entry(frame_left); entry_name.pack(fill=tk.X, pady=2)
    ttk.Label(frame_left, text="Prix :").pack(anchor=tk.W)
    entry_price = ttk.Entry(frame_left); entry_price.pack(fill=tk.X, pady=2)
    ttk.Label(frame_left, text="Quantité :").pack(anchor=tk.W)
    entry_qty = ttk.Entry(frame_left); entry_qty.pack(fill=tk.X, pady=2)
    ttk.Button(frame_left, text="Ajouter", command=action_add_product).pack(pady=10, fill=tk.X)

    # --- Zone Droite : Tableau ---
    frame_right = ttk.Frame(root)
    frame_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Recherche
    frame_search = ttk.Frame(frame_right)
    frame_search.pack(fill=tk.X, pady=5)
    global entry_search
    ttk.Label(frame_search, text="Recherche :").pack(side=tk.LEFT)
    entry_search = ttk.Entry(frame_search)
    entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    ttk.Button(frame_search, text="Go", command=action_search_product).pack(side=tk.LEFT)
    ttk.Button(frame_search, text="Reset", command=lambda: refresh_tree()).pack(side=tk.LEFT)

    # Treeview
    global tree
    tree = ttk.Treeview(frame_right, columns=('name', 'price', 'qty'), show='headings')
    tree.heading('name', text='Nom', command=lambda: action_sort_products('name'))
    tree.heading('price', text='Prix', command=lambda: action_sort_products('price'))
    tree.heading('qty', text='Quantité', command=lambda: action_sort_products('qty'))
    tree.pack(fill=tk.BOTH, expand=True)

    refresh_tree()

def display_login_screen():
    """Construit l'écran de connexion."""
    clear_window()
    root.geometry("400x350")
    root.title("Connexion Sécurisée")

    # Cadre centré
    login_frame = ttk.Frame(root, padding="20")
    login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    ttk.Label(login_frame, text="🔐 AUTHENTIFICATION", font=('Arial', 12, 'bold')).pack(pady=20)

    ttk.Label(login_frame, text="Utilisateur (admin) :").pack(anchor=tk.W)
    user_entry = ttk.Entry(login_frame)
    user_entry.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(login_frame, text="Mot de passe (admin123) :").pack(anchor=tk.W)
    pwd_entry = ttk.Entry(login_frame, show="*")
    pwd_entry.pack(fill=tk.X, pady=(0, 20))

    def on_login_click():
        attempt_login(user_entry.get(), pwd_entry.get())

    ttk.Button(login_frame, text="SE CONNECTER", command=on_login_click).pack(fill=tk.X)
    
    ttk.Label(login_frame, text="Vérification API HIBP active", font=("Arial", 8), foreground="grey").pack(pady=10)

def run_application():
    global root
    root = tk.Tk()
    
    # On commence par afficher le login
    display_login_screen()
    
    root.mainloop()

if __name__ == "__main__":
    run_application()