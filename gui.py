import tkinter as tk
from tkinter import ttk, messagebox
from inventory_manager import InventoryManager
from auth import check_pwned_password, hash_password, verify_password

# --- CONFIGURATION (Simulation Base de données) ---
ADMIN_USER = "admin"
# On simule un mot de passe haché pour "admin123"
SALT_SIMUL, HASH_SIMUL = hash_password("admin123")

# --- VARIABLES GLOBALES ---
inventory_mgr = InventoryManager("products.csv")
root = None

# Variables pour les champs de texte
entry_user = None
entry_pwd = None
entry_name = None
entry_price = None
entry_qty = None
entry_search = None
tree = None

# ==========================================
# 1. ÉCRAN DE CONNEXION (LOGIN)
# ==========================================

def display_login_screen():
    """Affiche l'écran de connexion au démarrage."""
    # Nettoyer la fenêtre
    for widget in root.winfo_children():
        widget.destroy()
        
    root.title("Connexion Sécurisée 🔒")
    root.geometry("400x350")

    # Cadre principal centré
    frame = ttk.Frame(root, padding="20")
    frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    ttk.Label(frame, text="AUTHENTIFICATION", font=("Arial", 14, "bold")).pack(pady=20)

    # Champ Utilisateur
    ttk.Label(frame, text="Identifiant :").pack(anchor=tk.W)
    global entry_user
    entry_user = ttk.Entry(frame)
    entry_user.pack(fill=tk.X, pady=(0, 10))

    # Champ Mot de passe
    ttk.Label(frame, text="Mot de passe :").pack(anchor=tk.W)
    global entry_pwd
    entry_pwd = ttk.Entry(frame, show="*")
    entry_pwd.pack(fill=tk.X, pady=(0, 20))

    # Bouton Connexion
    btn = ttk.Button(frame, text="SE CONNECTER", command=attempt_login)
    btn.pack(fill=tk.X, pady=5)
    
    ttk.Label(frame, text="(admin / admin123)", foreground="grey").pack(pady=5)

def attempt_login():
    """Vérifie le mot de passe et l'API de sécurité (Jalon 4)."""
    username = entry_user.get()
    password = entry_pwd.get()

    if not username or not password:
        messagebox.showwarning("Erreur", "Veuillez remplir les champs.")
        return

    # --- ÉTAPE 1 : Jalon 4 (Vérification API HIBP) ---
    # On vérifie si le mot de passe est compromis AVANT ou PENDANT la connexion
    leak_count = check_pwned_password(password)
    
    if leak_count > 0:
        messagebox.showwarning(
            "ALERTE SÉCURITÉ 🚨", 
            f"Ce mot de passe a été trouvé {leak_count} fois dans des fuites de données !\n\n"
            "Même si c'est le bon mot de passe, vous devriez le changer."
        )
    elif leak_count == -1:
        print("Erreur de connexion à l'API de sécurité.")

    # --- ÉTAPE 2 : Vérification Identifiants ---
    if username == ADMIN_USER and verify_password(SALT_SIMUL, HASH_SIMUL, password):
        messagebox.showinfo("Succès", "Connexion réussie.")
        display_dashboard_screen() # On passe à l'écran suivant
    else:
        messagebox.showerror("Erreur", "Identifiant ou mot de passe incorrect.")


# ==========================================
# 2. ÉCRAN PRINCIPAL (DASHBOARD)
# ==========================================

def display_dashboard_screen():
    """Affiche l'interface de gestion (après connexion)."""
    # Nettoyer la fenêtre (enlever le login)
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Gestion d'Inventaire - Admin")
    root.geometry("900x600")

    # --- En-tête ---
    header = ttk.Frame(root, padding=10)
    header.pack(fill=tk.X)
    ttk.Label(header, text="TABLEAU DE BORD", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
    ttk.Button(header, text="Déconnexion", command=display_login_screen).pack(side=tk.RIGHT)

    # --- Zone Principale ---
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # COLONNE GAUCHE : AJOUT
    left_col = ttk.LabelFrame(main_frame, text="Ajouter Produit", padding=10)
    left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

    global entry_name, entry_price, entry_qty
    ttk.Label(left_col, text="Nom:").pack(anchor=tk.W)
    entry_name = ttk.Entry(left_col); entry_name.pack(fill=tk.X, pady=5)
    
    ttk.Label(left_col, text="Prix:").pack(anchor=tk.W)
    entry_price = ttk.Entry(left_col); entry_price.pack(fill=tk.X, pady=5)
    
    ttk.Label(left_col, text="Quantité:").pack(anchor=tk.W)
    entry_qty = ttk.Entry(left_col); entry_qty.pack(fill=tk.X, pady=5)
    
    ttk.Button(left_col, text="Ajouter", command=action_add).pack(fill=tk.X, pady=15)

    # COLONNE DROITE : TABLEAU
    right_col = ttk.Frame(main_frame)
    right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Barre de recherche
    search_frame = ttk.Frame(right_col)
    search_frame.pack(fill=tk.X, pady=(0, 10))
    ttk.Label(search_frame, text="Recherche:").pack(side=tk.LEFT)
    global entry_search
    entry_search = ttk.Entry(search_frame)
    entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    ttk.Button(search_frame, text="Chercher", command=action_search).pack(side=tk.LEFT)
    ttk.Button(search_frame, text="Voir Tout", command=lambda: refresh_table()).pack(side=tk.LEFT)

    # Tableau
    global tree
    cols = ('name', 'price', 'qty')
    tree = ttk.Treeview(right_col, columns=cols, show='headings')
    tree.heading('name', text='Nom', command=lambda: action_sort('name'))
    tree.heading('price', text='Prix', command=lambda: action_sort('price'))
    tree.heading('qty', text='Quantité', command=lambda: action_sort('qty'))
    tree.pack(fill=tk.BOTH, expand=True)

    # Charger les données
    refresh_table()

# --- FONCTIONS LOGIQUES DU DASHBOARD ---

def refresh_table(data=None):
    for item in tree.get_children():
        tree.delete(item)
    products = data if data is not None else inventory_mgr.display_products()
    for p in products:
        tree.insert('', tk.END, values=(p.get('name'), p.get('price'), p.get('qty')))

def action_add():
    try:
        n, p, q = entry_name.get(), float(entry_price.get()), int(entry_qty.get())
        inventory_mgr.add_product({'name': n, 'price': str(p), 'qty': str(q)})
        entry_name.delete(0, tk.END); entry_price.delete(0, tk.END); entry_qty.delete(0, tk.END)
        refresh_table()
        messagebox.showinfo("OK", "Produit ajouté")
    except ValueError:
        messagebox.showerror("Erreur", "Prix ou quantité invalide")

def action_search():
    refresh_table(inventory_mgr.search_product(entry_search.get()))

def action_sort(key):
    inventory_mgr.sort_products(key)
    refresh_table()

# ==========================================
# 3. LANCEMENT
# ==========================================

def run_application():
    global root
    root = tk.Tk()
    
    # C'est ICI que tout se décide : on appelle le LOGIN en premier
    display_login_screen()
    
    root.mainloop()

if __name__ == "__main__":
    run_application()