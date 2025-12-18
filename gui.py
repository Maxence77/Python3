import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Imports locaux (assure-toi que auth.py, products.py, orders.py sont à jour)
import products
import auth
import orders

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ERP Gestion - Groupe 3")
        self.geometry("1200x850") 

        self.current_user = None
        self.is_admin_session = False
        
        # Variable pour stocker l'ID de la commande en cours de modification
        self.editing_order_id = None 

        style = ttk.Style()
        style.theme_use('clam')
        self.bg_color = "#f0f2f5"
        self.configure(bg=self.bg_color)

        self.show_login()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ==========================
    # LOGIN / SIGNUP
    # ==========================
    def show_login(self):
        self.clear_window()
        frame = tk.Frame(self, bg="white", padx=40, pady=40, relief="raised")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="GROUPE3 ERP", font=("Arial", 18, "bold"), bg="white").pack(pady=20)
        tk.Label(frame, text="Utilisateur", bg="white").pack(anchor="w")
        self.entry_user = ttk.Entry(frame, width=30); self.entry_user.pack(pady=5)
        tk.Label(frame, text="Mot de passe", bg="white").pack(anchor="w")
        self.entry_pass = ttk.Entry(frame, width=30, show="*"); self.entry_pass.pack(pady=5)
        
        tk.Button(frame, text="CONNEXION", bg="#2c3e50", fg="white", command=self.perform_login).pack(pady=15, fill="x")
        tk.Button(frame, text="Créer un compte", bg="white", command=self.perform_signup).pack()

    def perform_login(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        
        # On récupère le statut qui peut être FAIL, SUCCESS ou WARNING
        status, is_admin, token = auth.authenticate_user(u, p)
        
        if status == "FAIL": 
            messagebox.showerror("Erreur", "Login incorrect")
            
        elif status == "WARNING":
            # Login réussi, mais mot de passe dangereux
            messagebox.showwarning("⚠️ ATTENTION SÉCURITÉ", 
                                   "Connexion réussie, MAIS votre mot de passe a été trouvé dans une fuite de données (HaveIBeenPwned).\n\nVeuillez le changer immédiatement dans votre Profil !")
            self.current_user = u
            self.is_admin_session = is_admin
            self.show_main_interface()
            
        else: # SUCCESS
            self.current_user = u
            self.is_admin_session = is_admin
            self.show_main_interface()
    def perform_signup(self):
        u, p = self.entry_user.get(), self.entry_pass.get()
        if u and p:
            code, msg = auth.create_user(u, p)
            if code == "SUCCESS": messagebox.showinfo("OK", "Compte créé")
            else: messagebox.showerror("Erreur", msg)
        else: messagebox.showwarning("Info", "Remplir les champs")

    # ==========================
    # INTERFACE PRINCIPALE
    # ==========================
    def show_main_interface(self):
        self.clear_window()
        # Header
        h = tk.Frame(self, bg="#2c3e50", height=60); h.pack(fill="x")
        role = "ADMIN" if self.is_admin_session else "USER"
        tk.Label(h, text=f"👤 {self.current_user} ({role})", bg="#2c3e50", fg="white", font=("Bold", 12)).pack(side="left", padx=20)
        tk.Button(h, text="Déconnexion", command=self.show_login, bg="#c0392b", fg="white").pack(side="right", padx=10, pady=10)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_orders = ttk.Frame(self.notebook)
        self.tab_products = ttk.Frame(self.notebook)
        self.tab_profile = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_orders, text="Commandes")
        self.notebook.add(self.tab_products, text="Produits")
        self.notebook.add(self.tab_profile, text="Profil")

        if self.is_admin_session:
            self.tab_admin = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_admin, text="ADMINISTRATION")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.load_dashboard_view()
        self.check_messages()

    def on_tab_change(self, event):
        tab = self.notebook.tab(self.notebook.select(), "text")
        if tab == "Dashboard": self.load_dashboard_view()
        elif tab == "Commandes": self.load_orders_view()
        elif tab == "Produits": self.load_products_view()
        elif tab == "Profil": self.load_profile_view()
        elif tab == "ADMINISTRATION": self.load_admin_view()

    def check_messages(self):
        msgs = auth.get_user_messages(self.current_user)
        for m in msgs: messagebox.showwarning("Message Admin", m)

    # ==========================
    # 1. DASHBOARD
    # ==========================
    def load_dashboard_view(self):
        for w in self.tab_dashboard.winfo_children(): w.destroy()
        
        df = orders.load_orders()
        
        # KPI
        kf = tk.Frame(self.tab_dashboard, bg=self.bg_color); kf.pack(fill="x", pady=10)
        ca = df["Prix Total"].sum() if not df.empty else 0
        self.create_kpi(kf, "Chiffre d'Affaires", f"{ca:.2f} €", "#27ae60", 0)

        # Graphes
        gf = tk.Frame(self.tab_dashboard, bg=self.bg_color); gf.pack(fill="both", expand=True)
        
        if not df.empty and "Date" in df.columns:
            try:
                # --- CORRECTION DATE WARNING ---
                # On force le format explicite pour éviter le UserWarning
                df['DateObj'] = pd.to_datetime(df['Date'], format="%d/%m/%Y", errors='coerce')
                
                # Nettoyage des dates invalides
                df = df.dropna(subset=['DateObj'])
                
                if not df.empty:
                    # Tri par date
                    df = df.sort_values(by="DateObj")
                    
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), facecolor=self.bg_color)
                    
                    # Graph 1: Top Produits
                    df.groupby("Produit")["Quantité"].sum().plot(kind='bar', ax=ax1, color='#3498db')
                    ax1.set_title("Top Produits")
                    ax1.tick_params(axis='x', rotation=0)

                    # Graph 2: Evolution Ventes
                    daily_sales = df.groupby('DateObj')["Prix Total"].sum()
                    
                    ax2.plot(daily_sales.index, daily_sales.values, marker='o', color='#e74c3c', linestyle='-')
                    ax2.set_title("Ventes par Jour")
                    ax2.grid(True, linestyle='--', alpha=0.7)
                    
                    # Formatage des dates sur l'axe X
                    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                    ax2.tick_params(axis='x', rotation=45)
                    
                    canvas = FigureCanvasTkAgg(fig, master=gf)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True)
                    plt.close(fig)
                else: tk.Label(gf, text="Données dates vides ou invalides").pack()
            except Exception as e:
                print(e)
                tk.Label(gf, text=f"Erreur graphe: {e}").pack()
        else:
            tk.Label(gf, text="Pas de données").pack()

    def create_kpi(self, p, t, v, c, idx):
        f = tk.Frame(p, bg="white", relief="raised", padx=20, pady=10)
        f.grid(row=0, column=idx, padx=20, sticky="ew")
        tk.Label(f, text=t, fg="gray").pack()
        tk.Label(f, text=v, fg=c, font=("Bold", 16)).pack()

    # ==========================
    # 2. COMMANDES
    # ==========================
    def load_orders_view(self):
        for w in self.tab_orders.winfo_children(): w.destroy()
        
        # Titre dynamique
        mode_text = f"MODIFIER LA COMMANDE (ID: {self.editing_order_id})" if self.editing_order_id else "NOUVELLE COMMANDE"
        bg_color = "#f39c12" if self.editing_order_id else "#2c3e50"
        
        f = ttk.LabelFrame(self.tab_orders, text=mode_text)
        f.pack(fill="x", padx=10, pady=10)
        
        # Chargement Produits
        df_p = products.load_products()
        prods = df_p["Nom"].tolist() if not df_p.empty else []
        
        tk.Label(f, text="Produit:").pack(side="left")
        self.cb_order_prod = ttk.Combobox(f, values=prods, state="readonly")
        self.cb_order_prod.pack(side="left", padx=5)
        
        tk.Label(f, text="Qté:").pack(side="left")
        self.en_order_qty = ttk.Entry(f, width=5)
        self.en_order_qty.pack(side="left", padx=5)
        
        # Bouton Action
        btn_text = "Sauvegarder Modification" if self.editing_order_id else "Créer Commande"
        tk.Button(f, text=btn_text, command=self.save_order, bg=bg_color, fg="white").pack(side="left", padx=20)
        
        # Bouton Annuler (si mode édition)
        if self.editing_order_id:
            tk.Button(f, text="Annuler", command=self.cancel_edit).pack(side="left")

        # Liste
        tb = tk.Frame(self.tab_orders, pady=5); tb.pack(fill="x", padx=10)
        tk.Button(tb, text="✏️ Modifier la sélection", command=self.load_order_into_form, bg="#f1c40f").pack(side="right")

        cols = ("ID", "Date", "Produit", "Quantité", "Total", "Client")
        self.tree_orders = ttk.Treeview(self.tab_orders, columns=cols, show="headings")
        for c in cols: self.tree_orders.heading(c, text=c)
        self.tree_orders.pack(fill="both", expand=True, padx=10)
        
        df = orders.load_orders()
        if not df.empty:
            for _, r in df.iloc[::-1].iterrows():
                self.tree_orders.insert("", "end", values=(r["ID"], r["Date"], r["Produit"], r["Quantité"], r["Prix Total"], r.get("Client","?")))

    def save_order(self):
        prod = self.cb_order_prod.get()
        qty = self.en_order_qty.get()
        
        if not prod or not qty: return

        if self.editing_order_id:
            ok, msg = orders.update_order(self.editing_order_id, prod, qty)
            if ok:
                messagebox.showinfo("Succès", "Commande modifiée !")
                self.editing_order_id = None
                self.load_orders_view()
            else:
                messagebox.showerror("Erreur", msg)
        else:
            ok, msg = orders.create_order(self.current_user, prod, qty)
            if ok:
                messagebox.showinfo("Succès", "Commande ajoutée")
                self.load_orders_view()
            else:
                messagebox.showerror("Erreur", msg)

    def load_order_into_form(self):
        sel = self.tree_orders.selection()
        if not sel: return messagebox.showwarning("Info", "Sélectionnez une commande")
        
        item = self.tree_orders.item(sel[0])
        vals = item['values']
        self.editing_order_id = vals[0]
        self.load_orders_view()
        self.cb_order_prod.set(vals[2])
        self.en_order_qty.insert(0, vals[3])

    def cancel_edit(self):
        self.editing_order_id = None
        self.load_orders_view()

    # ==========================
    # 3. PRODUITS (AJOUT / MODIF / SUPPR)
    # ==========================
    def load_products_view(self):
        for w in self.tab_products.winfo_children(): w.destroy()
        
        bar = tk.Frame(self.tab_products, pady=5); bar.pack(fill="x")
        tk.Button(bar, text="Ajouter", command=self.pop_prod_add, bg="#27ae60", fg="white").pack(side="left")
        tk.Button(bar, text="Modifier", command=self.pop_prod_edit, bg="#f39c12", fg="white").pack(side="left", padx=5)
        tk.Button(bar, text="Supprimer", command=self.del_prod, bg="#c0392b", fg="white").pack(side="left", padx=5)
        
        cols = ("Nom", "Catégorie", "Prix", "Quantité")
        self.tree_prods = ttk.Treeview(self.tab_products, columns=cols, show="headings")
        for c in cols: self.tree_prods.heading(c, text=c)
        self.tree_prods.pack(fill="both", expand=True, padx=10)
        
        for _, r in products.load_products().iterrows():
            self.tree_prods.insert("", "end", values=(r["Nom"], r["Catégorie"], r["Prix"], r["Quantité"]))

    def pop_prod_add(self):
        self.open_prod_popup("Ajouter Produit")

    def pop_prod_edit(self):
        sel = self.tree_prods.selection()
        if not sel: return messagebox.showwarning("Info", "Sélectionnez un produit")
        vals = self.tree_prods.item(sel[0])['values']
        self.open_prod_popup("Modifier Produit", vals)

    def open_prod_popup(self, title, data=None):
        w = tk.Toplevel(self); w.title(title)
        
        tk.Label(w, text="Nom").pack(); n = ttk.Entry(w); n.pack()
        tk.Label(w, text="Cat").pack(); c = ttk.Entry(w); c.pack()
        tk.Label(w, text="Prix").pack(); p = ttk.Entry(w); p.pack()
        tk.Label(w, text="Qté").pack(); q = ttk.Entry(w); q.pack()

        old_name = None
        if data:
            n.insert(0, data[0]); old_name = data[0]
            c.insert(0, data[1])
            p.insert(0, data[2])
            q.insert(0, data[3])

        def save():
            try:
                name, cat, price, qty = n.get(), c.get(), float(p.get()), int(q.get())
                if old_name: 
                    # Appel de la fonction de modification complète (nécessite update dans products.py)
                    ok, msg = products.update_product_full(old_name, name, cat, price, qty)
                else:
                    products.add_product(name, cat, price, qty)
                    ok, msg = True, "Ajouté"

                if ok:
                    w.destroy()
                    self.load_products_view()
                else:
                    messagebox.showerror("Erreur", msg)
            except ValueError:
                messagebox.showerror("Erreur", "Prix/Qté doivent être des nombres")
            except Exception as e:
                # Fallback si update_product_full n'existe pas encore dans products.py
                messagebox.showerror("Erreur", f"Erreur backend: {e}")

        tk.Button(w, text="Valider", command=save, bg="#2c3e50", fg="white").pack(pady=10)

    def del_prod(self):
        s = self.tree_prods.selection()
        if s and messagebox.askyesno("Sur?", "Supprimer le produit ?"):
            products.delete_product(self.tree_prods.item(s[0])['values'][0])
            self.load_products_view()

    # ==========================
    # 4. PROFIL
    # ==========================
    def load_profile_view(self):
        for w in self.tab_profile.winfo_children(): w.destroy()
        
        frame = tk.Frame(self.tab_profile, bg="white", padx=20, pady=20, relief="groove")
        frame.pack(pady=40)

        tk.Label(frame, text=f"Profil connecté : {self.current_user}", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        tk.Label(frame, text="Nouveau mot de passe :", bg="white").pack(anchor="w")
        self.entry_new_pass = ttk.Entry(frame, show="●", width=25)
        self.entry_new_pass.pack(pady=5)
        
        tk.Button(frame, text="Changer MDP", command=self.perform_pass_change, bg="#2980b9", fg="white").pack(pady=15, fill="x")

    def perform_pass_change(self):
        new_p = self.entry_new_pass.get()
        if not new_p: 
            messagebox.showwarning("Attention", "Veuillez entrer un mot de passe.")
            return

        # Appel au backend
        status, msg = auth.change_password(self.current_user, new_p)
        
        if status == "SUCCESS":
            messagebox.showinfo("Succès", msg)
            self.entry_new_pass.delete(0, 'end') # Vide le champ
        else:
            messagebox.showerror("Erreur Sécurité", msg)

    # ==========================
    # 5. ADMINISTRATION
    # ==========================
    def load_admin_view(self):
        for w in self.tab_admin.winfo_children(): w.destroy()

        bar = tk.Frame(self.tab_admin, bg="#34495e", pady=10); bar.pack(fill="x")
        
        # Boutons Admin
        tk.Button(bar, text="📧 Envoyer Msg", command=self.adm_msg).pack(side="right", padx=5)
        tk.Button(bar, text="👑 Changer Rôle (Admin/User)", command=self.adm_toggle_role, bg="#f1c40f").pack(side="right", padx=5)
        tk.Button(bar, text="❌ Supprimer User", command=self.adm_del, bg="#c0392b", fg="white").pack(side="right", padx=5)

        cols = ("Username", "Admin", "Compromised")
        self.tree_users = ttk.Treeview(self.tab_admin, columns=cols, show="headings")
        for c in cols: self.tree_users.heading(c, text=c)
        self.tree_users.pack(fill="both", expand=True, padx=10)

        for _, r in auth.load_users().iterrows():
            is_adm = str(r.get("Admin", False)).lower() in ['true', '1', 'yes']
            disp_adm = "OUI 👑" if is_adm else "NON"
            self.tree_users.insert("", "end", values=(r["Username"], disp_adm, r["Compromised"]))

    def adm_toggle_role(self):
        sel = self.tree_users.selection()
        if not sel: return
        user = self.tree_users.item(sel[0])['values'][0]
        
        if messagebox.askyesno("Confirmation", f"Changer le statut Admin de {user} ?"):
            # Appel à auth.py (nouvelle fonction toggle_admin_status)
            try:
                ok, msg = auth.toggle_admin_status(user)
                if ok:
                    messagebox.showinfo("Succès", msg)
                    self.load_admin_view()
                else:
                    messagebox.showerror("Erreur", msg)
            except AttributeError:
                 messagebox.showerror("Erreur", "Fonction toggle_admin_status manquante dans auth.py")

    def adm_del(self):
        sel = self.tree_users.selection()
        if not sel: return
        user = self.tree_users.item(sel[0])['values'][0]
        if user == "admin": return messagebox.showerror("Stop", "Touche pas au patron.")
        if messagebox.askyesno("Sur?", f"Supprimer {user}?"):
            if auth.delete_user(user): self.load_admin_view()

    def adm_msg(self):
        s = self.tree_users.selection()
        if s:
            u = self.tree_users.item(s[0])['values'][0]
            m = simpledialog.askstring("Msg", "Message:")
            if m: auth.send_message(u, m)

if __name__ == "__main__":
    App().mainloop()
