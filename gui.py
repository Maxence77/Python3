import tkinter as tk
from tkinter import ttk, messagebox
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
        
        # --- CONFIGURATION DU STYLE (Module 4) ---
        style = ttk.Style()
        style.theme_use('clam')
        
        # Palette de couleurs
        self.bg_color = "#f0f2f5"
        self.header_color = "#2c3e50"
        self.accent_color = "#3498db"
        
        self.configure(bg=self.bg_color)
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Card.TFrame", background="white", relief="raised")
        
        self.show_login()

    def clear_window(self):
        """Nettoie tous les widgets de la fenêtre actuelle."""
        for widget in self.winfo_children():
            widget.destroy()

    # =========================================================================
    # PARTIE 1 : AUTHENTIFICATION & SÉCURITÉ (Module 3)
    # =========================================================================
    def show_login(self):
        self.clear_window()
        
        # Cadre central blanc
        frame = tk.Frame(self, bg="white", padx=40, pady=40, relief="raised", bd=1)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="GROUPE3 SECURITY", font=("Segoe UI", 18, "bold"), bg="white", fg=self.header_color).pack(pady=(0, 20))
        tk.Label(frame, text="Connexion Sécurisée", font=("Segoe UI", 10), bg="white", fg="gray").pack(pady=(0, 20))

        tk.Label(frame, text="Identifiant", bg="white", font=("bold")).pack(anchor="w")
        self.entry_user = ttk.Entry(frame, width=35)
        self.entry_user.pack(pady=5)

        tk.Label(frame, text="Mot de passe", bg="white", font=("bold")).pack(anchor="w")
        self.entry_pass = ttk.Entry(frame, width=35, show="●")
        self.entry_pass.pack(pady=5)

        # Boutons
        tk.Button(frame, text="SE CONNECTER", bg=self.header_color, fg="white", font=("Segoe UI", 10, "bold"), 
                  command=self.do_login, relief="flat", pady=5).pack(pady=15, fill="x")
        
        tk.Button(frame, text="Créer un compte", bg="white", fg=self.header_color, font=("Segoe UI", 9, "underline"), 
                  command=self.do_signup, relief="flat").pack(pady=0)

    def do_login(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        
        # Vérification via auth.py (Module 3 inclu)
        status = auth.check_login(u, p)
        
        if status == "OK" or status == "COMPROMISED":
            self.current_user = u
            self.show_main_interface()
            
            # ALERTE SÉCURITÉ (Module 3)
            if status == "COMPROMISED":
                messagebox.showwarning("⚠️ ALERTE DE SÉCURITÉ", 
                                       "Votre mot de passe a été trouvé dans une base de données piratée publique !\n\n"
                                       "Par sécurité, veuillez le changer immédiatement dans l'onglet 'Mon Profil'.")
        else:
            messagebox.showerror("Erreur", "Identifiant ou mot de passe incorrect.")

    def do_signup(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        
        if u and p:
            # Création avec vérification API Pwned (Module 3)
            result = auth.create_user(u, p)
            
            if result == "EXIST":
                messagebox.showerror("Erreur", "Cet utilisateur existe déjà.")
            else:
                # result contient le nombre de fois où le mdp a été vu (0 = safe)
                if result > 0:
                    messagebox.showwarning("Compte créé avec Risque", 
                                           f"Compte créé, MAIS ce mot de passe est apparu {result} fois dans des fuites de données.\n"
                                           "Il est fortement recommandé d'en changer.")
                else:
                    messagebox.showinfo("Succès", "Compte créé avec succès ! Connectez-vous.")
        else:
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs.")

    # =========================================================================
    # PARTIE 2 : INTERFACE PRINCIPALE (Module 4 - Layout & Tabs)
    # =========================================================================
    def show_main_interface(self):
        self.clear_window()
        
        # --- HEADER ---
        header = tk.Frame(self, bg=self.header_color, height=60)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text=f"👤 {self.current_user}", bg=self.header_color, fg="white", font=("Segoe UI", 12, "bold")).pack(side="left", padx=20)
        
        # Bouton Déconnexion
        tk.Button(header, text="Déconnexion", bg="#c0392b", fg="white", relief="flat", command=self.show_login).pack(side="right", padx=10, pady=10)
        
        # Bouton Admin (Visible seulement si admin)
        if self.current_user == "admin":
             tk.Button(header, text="ADMINISTRATION", bg="#e67e22", fg="white", relief="flat", command=self.show_admin_popup).pack(side="right", padx=10)

        # --- ONGLETS (NOTEBOOK) ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Création des frames pour chaque onglet
        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_orders = ttk.Frame(notebook)
        self.tab_products = ttk.Frame(notebook)
        self.tab_profile = ttk.Frame(notebook)

        # Ajout des onglets
        notebook.add(self.tab_dashboard, text=" 📊 Dashboard ")
        notebook.add(self.tab_orders, text=" 🛒 Commandes ")
        notebook.add(self.tab_products, text=" 📦 Produits ")
        notebook.add(self.tab_profile, text=" 🔒 Mon Profil ")

        # Chargement initial des vues
        self.load_dashboard_view()
        self.load_orders_view()
        self.load_products_view()
        self.load_profile_view()

    # =========================================================================
    # PARTIE 3 : STATISTIQUES & DASHBOARD (Module 5B)
    # =========================================================================
    def load_dashboard_view(self):
        # Nettoyage
        for widget in self.tab_dashboard.winfo_children(): widget.destroy()
        
        # Chargement données
        df_orders = orders.load_orders()
        df_products = products.load_products()
        
        # --- SECTION KPI (Indicateurs Clés) ---
        kpi_frame = tk.Frame(self.tab_dashboard, bg=self.bg_color)
        kpi_frame.pack(fill="x", pady=10)
        
        ca = df_orders["Prix Total"].sum() if not df_orders.empty else 0
        vol = df_orders["Quantité"].sum() if not df_orders.empty else 0
        stock_val = (df_products["Prix"] * df_products["Quantité"]).sum() if not df_products.empty else 0

        self.create_kpi_card(kpi_frame, "Chiffre d'Affaires", f"{ca:,.2f} €", "#27ae60", 0)
        self.create_kpi_card(kpi_frame, "Volume Ventes", f"{vol} Unités", "#2980b9", 1)
        self.create_kpi_card(kpi_frame, "Valeur Stock", f"{stock_val:,.2f} €", "#8e44ad", 2)

        # --- SECTION GRAPHIQUES ---
        chart_frame = tk.Frame(self.tab_dashboard, bg=self.bg_color)
        chart_frame.pack(fill="both", expand=True, pady=10)

        if not df_orders.empty:
            # Création Figure Matplotlib
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), facecolor=self.bg_color)
            
            # Graph 1: Top 5 Produits
            top5 = df_orders.groupby("Produit")["Quantité"].sum().nlargest(5)
            top5.plot(kind='bar', ax=ax1, color='#3498db')
            ax1.set_title("Top 5 Ventes")
            ax1.set_ylabel("Qté Vendue")
            ax1.tick_params(axis='x', rotation=45)
            
            # Graph 2: Évolution Ventes (Timeline)
            evo = df_orders.groupby("Date")["Prix Total"].sum()
            evo.plot(kind='line', marker='o', ax=ax2, color='#e74c3c')
            ax2.set_title("Évolution C.A.")
            ax2.grid(True, linestyle='--', alpha=0.6)
            
            # Intégration Tkinter
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(chart_frame, text="Pas assez de données pour les graphiques", font=("Segoe UI", 14)).pack(pady=50)

    def create_kpi_card(self, parent, title, value, color, col):
        card = tk.Frame(parent, bg="white", relief="raised", bd=1, padx=20, pady=15)
        card.grid(row=0, column=col, padx=20, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)
        
        tk.Label(card, text=title, bg="white", fg="gray", font=("Segoe UI", 10)).pack()
        tk.Label(card, text=value, bg="white", fg=color, font=("Segoe UI", 18, "bold")).pack()

    # =========================================================================
    # PARTIE 4 : GESTION DES COMMANDES (Module 5A)
    # =========================================================================
    def load_orders_view(self):
        for widget in self.tab_orders.winfo_children(): widget.destroy()

        # Zone Formulaire Commande
        form_frame = ttk.LabelFrame(self.tab_orders, text="Nouvelle Commande")
        form_frame.pack(fill="x", padx=10, pady=10)

        df_p = products.load_products()
        prod_list = df_p["Nom"].tolist() if not df_p.empty else []

        # Sélecteur Produit
        ttk.Label(form_frame, text="Produit :").pack(side="left", padx=10)
        self.cb_prod = ttk.Combobox(form_frame, values=prod_list, state="readonly", width=25)
        self.cb_prod.pack(side="left", padx=5)

        # Entrée Quantité
        ttk.Label(form_frame, text="Quantité :").pack(side="left", padx=10)
        self.ent_qty = ttk.Entry(form_frame, width=10)
        self.ent_qty.pack(side="left", padx=5)

        # Bouton Valider
        tk.Button(form_frame, text="✅ Valider la Commande", bg="#27ae60", fg="white", relief="flat",
                  command=self.submit_order).pack(side="left", padx=20)

        # Historique
        ttk.Label(self.tab_orders, text="Historique des Transactions", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        
        cols = ("ID", "Date", "Produit", "Quantité", "Prix Total", "Client")
        self.tree_orders = ttk.Treeview(self.tab_orders, columns=cols, show="headings")
        for c in cols: self.tree_orders.heading(c, text=c)
        self.tree_orders.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_orders_list()

    def submit_order(self):
        prod = self.cb_prod.get()
        qty = self.ent_qty.get()
        
        if not prod or not qty:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit et une quantité.")
            return

        # Appel Logique Module 5 (Vérif stock + Décrément)
        res = orders.create_order(self.current_user, prod, qty)
        
        if res == "OK":
            messagebox.showinfo("Succès", "Commande validée ! Stock mis à jour.")
            self.ent_qty.delete(0, 'end')
            # Tout rafraîchir
            self.refresh_orders_list()
            self.load_dashboard_view()
            self.load_products_view()
        else:
            messagebox.showerror("Erreur Commande", res)

    def refresh_orders_list(self):
        for i in self.tree_orders.get_children(): self.tree_orders.delete(i)
        df = orders.load_orders()
        if not df.empty:
            # Affichage inversé (plus récent en haut)
            for _, row in df.iloc[::-1].iterrows():
                self.tree_orders.insert("", "end", values=(row["ID"], row["Date"], row["Produit"], 
                                                           row["Quantité"], f"{row['Prix Total']} €", row["Client"]))

    # =========================================================================
    # PARTIE 5 : CATALOGUE PRODUITS (Module 4 - CRUD)
    # =========================================================================
    def load_products_view(self):
        for widget in self.tab_products.winfo_children(): widget.destroy()

        # Barre d'outils
        toolbar = tk.Frame(self.tab_products, bg="#dfe6e9", pady=5)
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="➕ Ajouter", command=self.popup_add_product, bg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="✏️ Modifier", command=self.popup_edit_product, bg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="🗑️ Supprimer", command=self.delete_product_action, bg="white", fg="red").pack(side="left", padx=5)
        tk.Button(toolbar, text="🔄 Actualiser", command=self.load_products_view, bg="white").pack(side="right", padx=5)

        # Tableau
        cols = ("Nom", "Catégorie", "Prix", "Quantité")
        self.tree_products = ttk.Treeview(self.tab_products, columns=cols, show="headings")
        for c in cols: self.tree_products.heading(c, text=c)
        self.tree_products.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Remplissage
        df = products.load_products()
        for _, row in df.iterrows():
            self.tree_products.insert("", "end", values=(row["Nom"], row["Catégorie"], f"{row['Prix']} €", row["Quantité"]))

    def popup_add_product(self):
        self.product_form_window("Ajouter un Produit")

    def popup_edit_product(self):
        sel = self.tree_products.selection()
        if not sel:
            messagebox.showwarning("Info", "Sélectionnez un produit à modifier")
            return
        
        vals = self.tree_products.item(sel[0])['values']
        # Nettoyage prix (enlève le €)
        price_clean = str(vals[2]).replace(" €", "")
        
        data = {"nom": vals[0], "cat": vals[1], "prix": price_clean, "qty": vals[3]}
        self.product_form_window("Modifier Produit", is_edit=True, old_data=data)

    def product_form_window(self, title, is_edit=False, old_data=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("400x350")
        
        tk.Label(win, text="Nom :").pack(pady=5)
        e_nom = ttk.Entry(win)
        e_nom.pack()
        
        tk.Label(win, text="Catégorie :").pack(pady=5)
        e_cat = ttk.Combobox(win, values=["Informatique", "Mobilier", "Vêtement", "Service"])
        e_cat.pack()
        
        tk.Label(win, text="Prix (€) :").pack(pady=5)
        e_prix = ttk.Entry(win)
        e_prix.pack()
        
        tk.Label(win, text="Quantité :").pack(pady=5)
        e_qty = ttk.Entry(win)
        e_qty.pack()

        # Pré-remplissage si modification
        if is_edit and old_data:
            e_nom.insert(0, old_data['nom'])
            e_cat.set(old_data['cat'])
            e_prix.insert(0, old_data['prix'])
            e_qty.insert(0, old_data['qty'])

        def save():
            try:
                nom, cat = e_nom.get(), e_cat.get()
                prix, qty = float(e_prix.get()), int(e_qty.get())
                
                if is_edit:
                    products.update_product(old_data['nom'], nom, cat, prix, qty)
                    messagebox.showinfo("Succès", "Produit modifié")
                else:
                    if products.add_product(nom, cat, prix, qty):
                        messagebox.showinfo("Succès", "Produit ajouté")
                    else:
                        messagebox.showerror("Erreur", "Produit déjà existant")
                
                win.destroy()
                self.load_products_view()
                self.load_orders_view() # Pour mettre à jour la combobox commande
            except ValueError:
                messagebox.showerror("Erreur", "Prix ou Quantité invalide")

        tk.Button(win, text="Sauvegarder", command=save, bg="#3498db", fg="white").pack(pady=20, fill="x", padx=50)

    def delete_product_action(self):
        sel = self.tree_products.selection()
        if sel:
            nom = self.tree_products.item(sel[0])['values'][0]
            if messagebox.askyesno("Confirmer", f"Supprimer {nom} ?"):
                products.delete_product(nom)
                self.load_products_view()

    # =========================================================================
    # PARTIE 6 : PROFIL UTILISATEUR & PASSWORD (Module 3)
    # =========================================================================
    def load_profile_view(self):
        for widget in self.tab_profile.winfo_children(): widget.destroy()

        card = ttk.LabelFrame(self.tab_profile, text="Gestion du Compte & Sécurité")
        card.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(card, text="Changer mon mot de passe", font=("Segoe UI", 12, "bold")).pack(pady=20)
        
        tk.Label(card, text="Nouveau mot de passe :").pack()
        new_pass = ttk.Entry(card, show="●")
        new_pass.pack(pady=5)
        
        def update_pass():
            pwd = new_pass.get()
            if pwd:
                # Appel auth.py (Module 3 - Check Pwned)
                count = auth.change_password(self.current_user, pwd)
                if count > 0:
                    messagebox.showwarning("Sécurité Faible", 
                                           f"Mot de passe mis à jour mais COMPROMIS ({count} fois dans des fuites).\n"
                                           "Veuillez en choisir un plus complexe !")
                else:
                    messagebox.showinfo("Parfait", "Mot de passe mis à jour et Sécurisé ✅")
                    new_pass.delete(0, 'end')
            else:
                messagebox.showerror("Erreur", "Champ vide")

        tk.Button(card, text="Mettre à jour le mot de passe", command=update_pass).pack(pady=15)
        
        tk.Label(card, text="ℹ️ Protection 'Have I Been Pwned' active.", fg="gray").pack(side="bottom", pady=20)

    # =========================================================================
    # PARTIE 7 : ADMINISTRATION (Module 3 & 4)
    # =========================================================================
    def show_admin_popup(self):
        win = tk.Toplevel(self)
        win.title("Administration Système")
        win.geometry("500x500")
        
        tk.Label(win, text="Gestion Utilisateurs", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Liste
        listbox = tk.Listbox(win, font=("Consolas", 10))
        listbox.pack(fill="both", expand=True, padx=20, pady=10)
        
        df_u = auth.load_users()
        for _, row in df_u.iterrows():
            u = row["Username"]
            # Visualisation du statut compromis pour l'admin
            status = "[⚠️ COMPROMIS]" if row["Compromised"] == "Oui" else "[OK]"
            if u == "admin": status = "[ADMIN]"
            
            listbox.insert("end", f"{u:<20} {status}")
            
        def del_user():
            sel = listbox.curselection()
            if sel:
                line = listbox.get(sel)
                user = line.split()[0] # Récupère juste le nom
                
                if user == "admin":
                    messagebox.showerror("Erreur", "Impossible de supprimer l'admin")
                else:
                    if messagebox.askyesno("Confirmer", f"Supprimer {user} ?"):
                        auth.delete_user(user)
                        win.destroy()
                        self.show_admin_popup() # Refresh

        tk.Button(win, text="Supprimer l'utilisateur sélectionné", command=del_user, bg="#c0392b", fg="white").pack(pady=10)

# Fonction de lancement
def run_gui():
    app = App()
    app.mainloop()

# À AJOUTER TOUT EN BAS DE gui.py
if __name__ == "__main__":
    run_gui()