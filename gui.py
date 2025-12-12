import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import products
import auth
import orders
import pandas as pd

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Groupe3 Enterprise ERP")
        self.geometry("1200x800")
        self.current_user = None
        
        # --- STYLE & THEME (Module 4) ---
        style = ttk.Style()
        style.theme_use('clam')
        
        # Couleurs et polices
        self.configure(bg="#f0f0f0")
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 11))
        style.configure("TButton", font=("Helvetica", 10, "bold"))
        style.configure("Header.TLabel", font=("Helvetica", 16, "bold"), foreground="#2c3e50")
        
        self.show_login()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ==========================================
    # MODULE 4: SÉCURITÉ & LOGIN
    # ==========================================
    def show_login(self):
        self.clear_window()
        
        # Cadre central
        frame = tk.Frame(self, bg="white", padx=40, pady=40, relief="raised", bd=2)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="🔒 CONNEXION SÉCURISÉE", font=("Arial", 16, "bold"), bg="white", fg="#34495e").pack(pady=(0, 20))

        tk.Label(frame, text="Identifiant", bg="white").pack(anchor="w")
        self.entry_user = ttk.Entry(frame, width=30)
        self.entry_user.pack(pady=5)

        tk.Label(frame, text="Mot de passe", bg="white").pack(anchor="w")
        self.entry_pass = ttk.Entry(frame, width=30, show="●")
        self.entry_pass.pack(pady=5)

        ttk.Button(frame, text="Se Connecter", command=self.do_login).pack(pady=15, fill="x")
        ttk.Button(frame, text="Créer un compte", command=self.do_signup).pack(pady=0, fill="x")

    def do_login(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        if auth.check_login(u, p):
            self.current_user = u
            self.show_main_interface()
        else:
            messagebox.showerror("Accès Refusé", "Identifiants invalides.")

    def do_signup(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        if u and p:
            if auth.create_user(u, p):
                messagebox.showinfo("Succès", "Compte créé avec succès.")
            else:
                messagebox.showerror("Erreur", "Utilisateur existant.")
        else:
            messagebox.showwarning("Validation", "Champs requis.")

    # ==========================================
    # MODULE 4: INTERFACE PRINCIPALE (GUI)
    # ==========================================
    def show_main_interface(self):
        self.clear_window()
        
        # Header Navigation
        nav = tk.Frame(self, bg="#2c3e50", height=60)
        nav.pack(side="top", fill="x")
        
        tk.Label(nav, text=f"👤 {self.current_user}", bg="#2c3e50", fg="white", font=("Arial", 12)).pack(side="left", padx=20)
        tk.Button(nav, text="Déconnexion", bg="#c0392b", fg="white", command=self.show_login, relief="flat").pack(side="right", padx=10, pady=10)
        
        if self.current_user == "admin":
             tk.Button(nav, text="ADMINISTRATION", bg="#e67e22", fg="white", command=self.show_admin_popup, relief="flat").pack(side="right", padx=10)

        # Onglets Principaux
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Création des onglets
        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_products = ttk.Frame(notebook)
        self.tab_orders = ttk.Frame(notebook)

        notebook.add(self.tab_dashboard, text="📊 Statistiques & Dashboard")
        notebook.add(self.tab_orders, text="🛒 Gestion des Commandes")
        notebook.add(self.tab_products, text="📦 Catalogue Produits")

        # Chargement des vues
        self.load_dashboard_view()
        self.load_orders_view()
        self.load_products_view()

    # ==========================================
    # MODULE 5 - PARTIE B: STATISTIQUES
    # ==========================================
    def load_dashboard_view(self):
        for widget in self.tab_dashboard.winfo_children(): widget.destroy()
        
        df_orders = orders.load_orders()
        df_products = products.load_products()
        
        # Header KPI
        kpi_frame = tk.Frame(self.tab_dashboard, bg="#ecf0f1", pady=10)
        kpi_frame.pack(fill="x")
        
        ca_total = df_orders["Prix Total"].sum() if not df_orders.empty else 0
        nb_ventes = df_orders["Quantité"].sum() if not df_orders.empty else 0
        nb_refs = len(df_products)
        
        self.create_kpi_card(kpi_frame, "Chiffre d'Affaires", f"{ca_total:,.2f} €", "#27ae60", 0)
        self.create_kpi_card(kpi_frame, "Volume Ventes", f"{nb_ventes} Unités", "#2980b9", 1)
        self.create_kpi_card(kpi_frame, "Références Actives", f"{nb_refs} Produits", "#8e44ad", 2)

        # Graphiques
        chart_frame = tk.Frame(self.tab_dashboard)
        chart_frame.pack(fill="both", expand=True, pady=10)

        if not df_orders.empty:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
            
            # Graph 1: Top 5 Produits (Bar)
            top5 = df_orders.groupby("Produit")["Quantité"].sum().nlargest(5)
            top5.plot(kind='bar', ax=ax1, color='#3498db')
            ax1.set_title("Top 5 Meilleures Ventes")
            ax1.set_xlabel("")
            
            # Graph 2: Évolution Ventes (Line)
            evo = df_orders.groupby("Date")["Prix Total"].sum()
            evo.plot(kind='line', marker='o', ax=ax2, color='#e74c3c')
            ax2.set_title("Évolution du CA par jour")
            ax2.grid(True)
            
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(chart_frame, text="Pas assez de données pour les graphiques", font=("Arial", 14)).pack(pady=50)

    def create_kpi_card(self, parent, title, value, color, col_index):
        card = tk.Frame(parent, bg="white", relief="raised", bd=1, padx=20, pady=10)
        card.grid(row=0, column=col_index, padx=20, sticky="ew")
        parent.grid_columnconfigure(col_index, weight=1)
        
        tk.Label(card, text=title, bg="white", fg="#7f8c8d").pack()
        tk.Label(card, text=value, bg="white", fg=color, font=("Arial", 18, "bold")).pack()

    # ==========================================
    # MODULE 5 - PARTIE A: COMMANDES
    # ==========================================
    def load_orders_view(self):
        for widget in self.tab_orders.winfo_children(): widget.destroy()

        # Zone Nouvelle Commande
        form_frame = ttk.LabelFrame(self.tab_orders, text="Nouvelle Commande")
        form_frame.pack(fill="x", padx=10, pady=10)
        
        df_p = products.load_products()
        product_list = df_p["Nom"].tolist() if not df_p.empty else []

        ttk.Label(form_frame, text="Produit:").pack(side="left", padx=5)
        self.combo_prod_order = ttk.Combobox(form_frame, values=product_list, state="readonly")
        self.combo_prod_order.pack(side="left", padx=5)

        ttk.Label(form_frame, text="Quantité:").pack(side="left", padx=5)
        self.qty_order_entry = ttk.Entry(form_frame, width=10)
        self.qty_order_entry.pack(side="left", padx=5)

        ttk.Button(form_frame, text="Valider Commande", command=self.submit_order).pack(side="left", padx=20)

        # Historique
        ttk.Label(self.tab_orders, text="Historique des Commandes", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        
        cols = ("ID", "Date", "Produit", "Quantité", "Prix Total", "Client")
        self.tree_orders = ttk.Treeview(self.tab_orders, columns=cols, show="headings")
        for c in cols: self.tree_orders.heading(c, text=c)
        self.tree_orders.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_orders_list()

    def submit_order(self):
        prod = self.combo_prod_order.get()
        qty = self.qty_order_entry.get()
        client = self.current_user
        
        if not prod or not qty:
            messagebox.showwarning("Attention", "Veuillez choisir un produit et une quantité.")
            return

        # Appel au module logique Orders
        result = orders.create_order(client, prod, qty)
        
        if result == "OK":
            messagebox.showinfo("Succès", "Commande enregistrée et stock mis à jour !")
            self.qty_order_entry.delete(0, 'end')
            self.refresh_orders_list()
            self.load_dashboard_view() # Refresh stats
            self.load_products_view()  # Refresh stock view
        else:
            messagebox.showerror("Erreur Commande", result)

    def refresh_orders_list(self):
        for i in self.tree_orders.get_children(): self.tree_orders.delete(i)
        df = orders.load_orders()
        # On affiche les plus récentes en premier
        if not df.empty:
            for _, row in df.iloc[::-1].iterrows():
                self.tree_orders.insert("", "end", values=(row["ID"], row["Date"], row["Produit"], row["Quantité"], f"{row['Prix Total']} €", row["Client"]))

    # ==========================================
    # MODULE 4: GESTION PRODUITS (CRUD + UI)
    # ==========================================
    def load_products_view(self):
        for widget in self.tab_products.winfo_children(): widget.destroy()

        # Barre d'outils
        toolbar = tk.Frame(self.tab_products, bg="#dfe6e9", height=40)
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="➕ Ajouter Produit", command=self.popup_add_product).pack(side="left", padx=5, pady=5)
        ttk.Button(toolbar, text="✏️ Modifier Sélection", command=self.popup_edit_product).pack(side="left", padx=5, pady=5)
        ttk.Button(toolbar, text="🗑️ Supprimer", command=self.delete_product_action).pack(side="left", padx=5, pady=5)
        
        ttk.Button(toolbar, text="🔄 Actualiser", command=self.refresh_products_list).pack(side="right", padx=5)

        # Tableau Produits
        cols = ("Nom", "Catégorie", "Prix", "Quantité")
        self.tree_products = ttk.Treeview(self.tab_products, columns=cols, show="headings")
        for c in cols: self.tree_products.heading(c, text=c)
        self.tree_products.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_products_list()

    def refresh_products_list(self):
        for i in self.tree_products.get_children(): self.tree_products.delete(i)
        df = products.load_products()
        for _, row in df.iterrows():
            self.tree_products.insert("", "end", values=(row["Nom"], row["Catégorie"], f"{row['Prix']} €", row["Quantité"]))

    def popup_add_product(self):
        self.product_form_window("Ajouter un produit")

    def popup_edit_product(self):
        selected = self.tree_products.selection()
        if not selected:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un produit à modifier.")
            return
        
        item = self.tree_products.item(selected[0])
        vals = item['values']
        # vals = [Nom, Categorie, Prix avec €, Quantité]
        
        # Nettoyage du prix pour l'édit
        raw_price = str(vals[2]).replace(" €", "")
        
        self.product_form_window("Modifier Produit", is_edit=True, 
                                 old_data={"nom": vals[0], "cat": vals[1], "prix": raw_price, "qty": vals[3]})

    def product_form_window(self, title, is_edit=False, old_data=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("400x300")
        
        tk.Label(win, text="Nom du Produit:").pack(pady=5)
        e_nom = ttk.Entry(win)
        e_nom.pack()
        if is_edit: e_nom.insert(0, old_data['nom'])

        tk.Label(win, text="Catégorie:").pack(pady=5)
        e_cat = ttk.Combobox(win, values=["Informatique", "Mobilier", "Vêtement", "Service"])
        e_cat.pack()
        if is_edit: e_cat.set(old_data['cat'])

        tk.Label(win, text="Prix (€):").pack(pady=5)
        e_prix = ttk.Entry(win)
        e_prix.pack()
        if is_edit: e_prix.insert(0, old_data['prix'])

        tk.Label(win, text="Quantité Stock:").pack(pady=5)
        e_qty = ttk.Entry(win)
        e_qty.pack()
        if is_edit: e_qty.insert(0, old_data['qty'])

        def save():
            try:
                nom = e_nom.get()
                cat = e_cat.get()
                prix = float(e_prix.get())
                qty = int(e_qty.get())
                
                if is_edit:
                    products.update_product(old_data['nom'], nom, cat, prix, qty)
                    messagebox.showinfo("Succès", "Produit modifié")
                else:
                    if products.add_product(nom, cat, prix, qty):
                        messagebox.showinfo("Succès", "Produit ajouté")
                    else:
                        messagebox.showerror("Erreur", "Ce produit existe déjà")
                
                win.destroy()
                self.refresh_products_list()
                self.load_orders_view() # Pour mettre à jour la combobox
            except ValueError:
                messagebox.showerror("Erreur", "Prix ou Quantité invalide")

        ttk.Button(win, text="Sauvegarder", command=save).pack(pady=20)

    def delete_product_action(self):
        selected = self.tree_products.selection()
        if selected:
            item = self.tree_products.item(selected[0])
            nom = item['values'][0]
            if messagebox.askyesno("Confirmation", f"Supprimer {nom} ?"):
                products.delete_product(nom)
                self.refresh_products_list()

    # ==========================================
    # POPUP ADMIN (Pour gérer les utilisateurs)
    # ==========================================
    def show_admin_popup(self):
        admin_win = tk.Toplevel(self)
        admin_win.title("Admin - Utilisateurs")
        admin_win.geometry("400x400")
        
        tk.Label(admin_win, text="Gestion Utilisateurs", font=("bold", 12)).pack(pady=10)
        
        listbox = tk.Listbox(admin_win)
        listbox.pack(fill="both", expand=True, padx=20)
        
        for u in auth.load_users()["Username"].values:
            listbox.insert("end", u)
            
        def del_u():
            sel = listbox.curselection()
            if sel:
                u = listbox.get(sel)
                if u == "admin":
                    messagebox.showerror("Stop", "Impossible de supprimer admin")
                else:
                    auth.delete_user(u)
                    listbox.delete(sel)
        
        ttk.Button(admin_win, text="Supprimer Utilisateur", command=del_u).pack(pady=10)

# Fonction de lancement
def run_gui():
    app = App()
    app.mainloop()