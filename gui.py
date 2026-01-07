import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import pandas as pd
import os

# Importation des modules réels du projet ERP Gestion
try:
    import stats
    import orders
    import products
    import auth
except ImportError:
    # Fallback si les fichiers ne sont pas trouvés lors du développement
    pass

# --- Configuration Visuelle ---
COLOR_PRIMARY = "#2c3e50"    # Bleu nuit professionnel
COLOR_SECONDARY = "#34495e"  # Gris-bleu
COLOR_ACCENT = "#3498db"     # Bleu clair (focus)
COLOR_BG = "#f5f6fa"         # Fond clair
COLOR_TEXT = "#ffffff"       # Texte blanc
COLOR_SUCCESS = "#27ae60"    # Vert succès

class ERPDataBridge:
    """Passerelle pour extraire les données réelles du projet ERP Gestion."""
    
    @staticmethod
    def get_sales_timeline():
        """Récupère l'historique complet des ventes groupées par date."""
        try:
            df = pd.read_csv("csv/orders.csv")
            if df.empty:
                return {'dates': [], 'values': []}
            
            # Conversion des dates
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Date'])
            
            # Groupement par date (Jour) pour une courbe lisible
            sales_by_date = df.groupby(df['Date'].dt.date)['Prix Total'].sum()
            
            return {
                'dates': sales_by_date.index.tolist(),
                'values': sales_by_date.values.tolist()
            }
        except Exception as e:
            print(f"Erreur timeline chart : {e}")
            return {'dates': [], 'values': []}

    @staticmethod
    def get_kpis():
        """Récupère les statistiques calculées par le module stats.py."""
        try:
            data = stats.get_global_stats()
            # Mapping pour assurer la compatibilité entre stats.py et le GUI
            return {
                "CA Total": data.get("chiffre_affaires", 0.0),
                "Valeur Stock": data.get("stock_valorisation", 0.0),
                "Nombre Commandes": data.get("commandes_count", 0),
                "Panier Moyen": data.get("panier_moyen", 0.0)
            }
        except Exception as e:
            print(f"Erreur stats.py : {e}")
            return {"CA Total": 0.0, "Valeur Stock": 0.0, "Panier Moyen": 0.0, "Nombre Commandes": 0}

class ERPApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw() # Cache la fenêtre principale tant que pas connecté

        self.title("ERP Gestion | Tableau de Bord Professionnel")
        self.geometry("1300x850")
        self.configure(bg=COLOR_BG)
        
        # État utilisateur
        self.current_user = None
        self.is_admin = False

        # Lancement de la connexion
        self.show_login_window()

    def show_login_window(self):
        """Affiche la fenêtre de connexion au démarrage."""
        login_win = tk.Toplevel(self)
        login_win.title("Connexion ERP")
        login_win.geometry("400x500")
        login_win.configure(bg=COLOR_PRIMARY)
        login_win.resizable(False, False)

        # Centrage de la fenêtre
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 500) // 2
        login_win.geometry(f"400x500+{x}+{y}")

        # Gestion de la fermeture (croix rouge)
        def on_close():
            self.destroy()
        login_win.protocol("WM_DELETE_WINDOW", on_close)

        # UI Connexion
        tk.Label(login_win, text="ERP GESTION", font=("Segoe UI", 24, "bold"), 
                 bg=COLOR_PRIMARY, fg="white").pack(pady=(60, 10))
        tk.Label(login_win, text="Connexion Sécurisée", font=("Segoe UI", 12), 
                 bg=COLOR_PRIMARY, fg="#bdc3c7").pack(pady=(0, 40))

        # Champs
        frame_input = tk.Frame(login_win, bg=COLOR_PRIMARY)
        frame_input.pack(pady=20)

        tk.Label(frame_input, text="Nom d'utilisateur", bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 10)).pack(anchor="w")
        e_user = tk.Entry(frame_input, font=("Segoe UI", 12), width=30)
        e_user.pack(pady=(5, 15), ipady=5)

        tk.Label(frame_input, text="Mot de passe", bg=COLOR_PRIMARY, fg="white", font=("Segoe UI", 10)).pack(anchor="w")
        e_pass = tk.Entry(frame_input, font=("Segoe UI", 12), width=30, show="*")
        e_pass.pack(pady=(5, 20), ipady=5)

        def attempt_login(event=None):
            username = e_user.get().strip()
            password = e_pass.get().strip()

            if not username or not password:
                messagebox.showwarning("Erreur", "Veuillez remplir tous les champs.", parent=login_win)
                return

            try:
                # auth.authenticate_user retourne (status, is_admin, token)
                status, is_admin, _ = auth.authenticate_user(username, password)
                
                if status in ["SUCCESS", "WARNING"]:
                    if status == "WARNING":
                        messagebox.showwarning("Alerte Sécurité", 
                            "Attention : Votre mot de passe a été détecté dans une fuite de données publique (Pwned) !\n\nNous vous recommandons de le changer immédiatement.", 
                            parent=login_win)
                    
                    # Connexion réussie
                    self.current_user = username
                    self.is_admin = is_admin
                    
                    login_win.destroy()
                    self._init_main_interface()
                    self.deiconify() # Affiche la fenêtre principale
                else:
                     messagebox.showerror("Echec", "Nom d'utilisateur ou mot de passe incorrect.", parent=login_win)
            except Exception as e:
                messagebox.showerror("Erreur Système", f"Impossible de se connecter : {e}", parent=login_win)

        # Bouton Connexion
        btn = tk.Button(login_win, text="SE CONNECTER", font=("Segoe UI", 11, "bold"), 
                        bg=COLOR_ACCENT, fg="white", relief="flat", cursor="hand2",
                        command=attempt_login)
        btn.pack(pady=10, ipadx=40, ipady=10)

        # Bouton Créer un compte
        tk.Button(login_win, text="Créer un compte", font=("Segoe UI", 10, "underline"), 
                  bg=COLOR_PRIMARY, fg="white", activebackground=COLOR_PRIMARY,
                  activeforeground=COLOR_ACCENT, relief="flat", cursor="hand2",
                  command=self.open_register_window).pack(pady=5)
        
        # Support touche Entrée
        login_win.bind('<Return>', attempt_login)

    def open_register_window(self):
        """Affiche la fenêtre d'inscription."""
        reg_win = tk.Toplevel(self)
        reg_win.title("Création de compte")
        reg_win.geometry("400x450")
        reg_win.configure(bg=COLOR_BG)
        
        # Centrage
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 450) // 2
        reg_win.geometry(f"+{x+20}+{y+20}") # Décalé légèrement par rapport au login

        tk.Label(reg_win, text="Nouvel Utilisateur", font=("Segoe UI", 18, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(pady=20)

        tk.Label(reg_win, text="Nom d'utilisateur", bg=COLOR_BG).pack(pady=5)
        e_user = tk.Entry(reg_win, width=30)
        e_user.pack(pady=5)

        tk.Label(reg_win, text="Mot de passe", bg=COLOR_BG).pack(pady=5)
        e_pass = tk.Entry(reg_win, width=30, show="*")
        e_pass.pack(pady=5)
        
        tk.Label(reg_win, text="Confirmer mot de passe", bg=COLOR_BG).pack(pady=5)
        e_pass_conf = tk.Entry(reg_win, width=30, show="*")
        e_pass_conf.pack(pady=5)

        def attempt_register():
            user = e_user.get().strip()
            pwd = e_pass.get().strip()
            pwd_conf = e_pass_conf.get().strip()

            if not user or not pwd:
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires.", parent=reg_win)
                return

            if pwd != pwd_conf:
                messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas.", parent=reg_win)
                return

            # Appel sécurisé au module auth
            try:
                status, msg = auth.create_user(user, pwd)
                if status == "SUCCESS":
                    messagebox.showinfo("Succès", msg, parent=reg_win)
                    reg_win.destroy()
                else:
                    messagebox.showerror("Erreur", msg, parent=reg_win)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la création : {e}", parent=reg_win)

        tk.Button(reg_win, text="CRÉER MON COMPTE", bg=COLOR_SUCCESS, fg="white", 
                  font=("Segoe UI", 10, "bold"), command=attempt_register).pack(pady=30)

    def _init_main_interface(self):
        """Initialise l'interface principale une fois connecté."""
        self._setup_styles()
        self._build_sidebar()
        self._build_main_content()

    def _setup_styles(self):
        """Configuration du thème visuel ttk."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Style des boutons de la barre latérale
        style.configure("Sidebar.TButton",
                        background=COLOR_SECONDARY,
                        foreground=COLOR_TEXT,
                        font=("Segoe UI", 11),
                        borderwidth=0,
                        padding=12)
        style.map("Sidebar.TButton", background=[('active', COLOR_ACCENT)])

        # Style des tableaux (Treeview)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_sidebar(self):
        """Construction de la navigation latérale."""
        sidebar = tk.Frame(self, bg=COLOR_PRIMARY, width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # En-tête / Logo
        header = tk.Frame(sidebar, bg=COLOR_PRIMARY, pady=30)
        header.pack(fill="x")
        tk.Label(header, text="ERP GESTION", bg=COLOR_PRIMARY, fg=COLOR_ACCENT, 
                 font=("Segoe UI", 20, "bold")).pack()

        # Éléments de navigation
        nav_items = [
            ("Tableau de Bord", "📊", self.show_dashboard),
            ("Commandes Clients", "📝", self.show_orders),
            ("Catalogue Produits", "📦", self.show_inventory),
            ("Messages", "💬", self.show_messages),
        ]
        
        # Menu spécifique Administrateur
        if self.is_admin:
             nav_items.append(("Admin", "🛠️", self.show_admin_panel))

        for text, icon, cmd in nav_items:
            btn = ttk.Button(sidebar, text=f"  {icon}  {text}", style="Sidebar.TButton", command=cmd)
            btn.pack(fill="x", padx=10, pady=5)

        # Pied de page sidebar
        info_zone = tk.Frame(sidebar, bg=COLOR_SECONDARY, pady=10)
        info_zone.pack(side="bottom", fill="x")
        
        user_status = "Administrateur" if self.is_admin else "Utilisateur"
        tk.Label(info_zone, text=f"{self.current_user} ({user_status})", bg=COLOR_SECONDARY, fg="white", font=("Segoe UI", 9)).pack()
        tk.Button(info_zone, text="Déconnexion", bg=COLOR_SECONDARY, fg="#e74c3c", relief="flat", 
                  command=self.logout).pack(pady=5)

    def logout(self):
        """Déconnecte l'utilisateur et retourne au login."""
        # On détruit l'interface actuelle
        for widget in self.winfo_children():
            widget.destroy()
        
        # On cache la fenêtre principale (qui est la racine)
        self.withdraw()
        
        # On réinitialise l'état
        self.current_user = None
        self.is_admin = False
        
        # On relance le login
        self.show_login_window()


    def _build_main_content(self):
        """Zone d'affichage dynamique."""
        self.container = tk.Frame(self, bg=COLOR_BG)
        self.container.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        self.show_dashboard()

    def clear_view(self):
        """Nettoie le conteneur principal avant de changer de vue."""
        for w in self.container.winfo_children():
            w.destroy()

    def show_dashboard(self):
        """Vue principale avec KPIs réels et graphique de vente."""
        self.clear_view()
        
        # Titre de la page
        top_bar = tk.Frame(self.container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 20))
        tk.Label(top_bar, text="Reporting & Analyses Ventes", font=("Segoe UI", 22, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(side="left")
        
        ttk.Button(top_bar, text="🔄 Actualiser les données", command=self.show_dashboard).pack(side="right")

        # Cartes KPI (Données issues de stats.py)
        kpi_data = ERPDataBridge.get_kpis()
        card_frame = tk.Frame(self.container, bg=COLOR_BG)
        card_frame.pack(fill="x", pady=10)

        self._add_kpi_card(card_frame, "Chiffre d'Affaires", f"{kpi_data.get('CA Total', 0):.2f} €", COLOR_SUCCESS, 0)
        self._add_kpi_card(card_frame, "Valeur du Stock", f"{kpi_data.get('Valeur Stock', 0):.2f} €", COLOR_ACCENT, 1)
        self._add_kpi_card(card_frame, "Volume Commandes", str(kpi_data.get('Nombre Commandes', 0)), "#e67e22", 2)

        # Graphique de Performance
        graph_box = tk.Frame(self.container, bg="white", highlightbackground="#dcdde1", highlightthickness=1)
        graph_box.pack(fill="both", expand=True, pady=20)
        
        self._render_chart(graph_box)

    def _add_kpi_card(self, parent, title, value, color, col):
        """Crée une carte de statistique moderne."""
        card = tk.Frame(parent, bg="white", padx=20, pady=20, highlightbackground="#dcdde1", highlightthickness=1)
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        tk.Label(card, text=title, font=("Segoe UI", 10, "bold"), bg="white", fg="#7f8c8d").pack(anchor="w")
        tk.Label(card, text=value, font=("Segoe UI", 20, "bold"), bg="white", fg=color).pack(anchor="w", pady=5)

    def _render_chart(self, parent):
        """Génère la courbe de performance historique."""
        # On nettoie le conteneur parent avant d'ajouter le canvas
        for widget in parent.winfo_children():
            widget.destroy()

        # On ferme les anciennes figures pour éviter les fuites de mémoire
        plt.close('all')

        try:
            data = ERPDataBridge.get_sales_timeline()
            dates = data.get('dates', [])
            values = data.get('values', [])
            
            fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
            fig.patch.set_facecolor('#ffffff')
            
            if dates:
                import matplotlib.dates as mdates
                
                # Courbe de performance (Ligne uniquement)
                ax.plot(dates, values, color=COLOR_PRIMARY, marker='o', markersize=4, linewidth=2, label="Ventes Journalières")
                
                # Remplissage sous la courbe pour effet "performance"
                ax.fill_between(dates, values, color=COLOR_PRIMARY, alpha=0.1)

                ax.set_title("Évolution des Ventes (Historique Complet)", fontsize=11, fontweight='bold', pad=15)
                
                # Formatage des dates sur l'axe X
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
                # Locator automatique pour éviter le chevauchement
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
                
            else:
                ax.text(0.5, 0.5, "Aucune donnée disponible", ha='center', va='center')

            ax.grid(axis='y', linestyle='--', alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            tk.Label(parent, text=f"Erreur graphique : {e}", fg="red").pack()
            print(f"Erreur render_chart: {e}")

    def show_orders(self):
        """Affiche le registre réel des commandes (orders.csv)."""
        self.clear_view()

        # Header avec bouton d'action
        header_frame = tk.Frame(self.container, bg=COLOR_BG)
        header_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(header_frame, text="Registre des Commandes Clients", font=("Segoe UI", 18, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(side="left")
        
        ttk.Button(header_frame, text="+ Nouvelle Commande", command=self.open_add_order_window).pack(side="right")

        try:
            df = pd.read_csv("csv/orders.csv")
            self._create_treeview(df)
        except Exception as e:
            tk.Label(self.container, text=f"Erreur de chargement des commandes : {e}", fg="red").pack()

    def show_inventory(self):
        """Affiche le catalogue de stock réel (products.csv)."""
        self.clear_view()
        
        # Header avec boutons d'action
        header_frame = tk.Frame(self.container, bg=COLOR_BG)
        header_frame.pack(fill="x", pady=(0, 20))

        tk.Label(header_frame, text="Gestion du Stock & Catalogue", font=("Segoe UI", 18, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(side="left")

        btn_frame = tk.Frame(header_frame, bg=COLOR_BG)
        btn_frame.pack(side="right")

        ttk.Button(btn_frame, text="Supprimer Sélection", command=self.delete_selected_product).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="+ Ajouter Produit", command=self.open_add_product_window).pack(side="right", padx=5)

        try:
            df = pd.read_csv("csv/products.csv")
            self.inventory_tree = self._create_treeview(df) # On garde une ref pour la suppression
        except Exception as e:
            tk.Label(self.container, text=f"Erreur de chargement des produits : {e}", fg="red").pack()

    def open_add_product_window(self):
        """Fenêtre modale pour ajouter un produit avec validations strictes."""
        win = tk.Toplevel(self)
        win.title("Nouveau Produit")
        win.geometry("400x450")
        win.configure(bg=COLOR_BG)

        # Formulaire
        tk.Label(win, text="Nom du produit (Lettres uniquement)", bg=COLOR_BG).pack(pady=5)
        e_nom = tk.Entry(win)
        e_nom.pack()

        tk.Label(win, text="Catégorie (Sans caractères spéciaux)", bg=COLOR_BG).pack(pady=5)
        e_cat = tk.Entry(win)
        e_cat.pack()

        tk.Label(win, text="Prix (€) (Chiffres uniquement)", bg=COLOR_BG).pack(pady=5)
        e_prix = tk.Entry(win)
        e_prix.pack()

        tk.Label(win, text="Quantité (Chiffres entiers uniquement)", bg=COLOR_BG).pack(pady=5)
        e_qty = tk.Entry(win)
        e_qty.pack()

        def save():
            nom = e_nom.get().strip()
            cat = e_cat.get().strip()
            prix_str = e_prix.get().strip()
            qty_str = e_qty.get().strip()
            
            # Validation déléguée au Backend (products.py) pour éviter la duplication de code
            # Le backend vérifie : Regex Nom/Cat, Type numérique Prix/Qté, Valeurs positives
            
            try:
                # On passe les valeurs brutes, le backend gère la conversion et la validation
                success, msg = products.add_product(nom, cat, prix_str, qty_str)
                
                if success:
                    messagebox.showinfo("Succès", msg)
                    win.destroy()
                    self.show_inventory() # Rafraichir
                else:
                    messagebox.showerror("Erreur", msg)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur inattendue : {e}")

        tk.Button(win, text="Enregistrer", bg=COLOR_SUCCESS, fg="white", command=save).pack(pady=20)

    def delete_selected_product(self):
        """Supprime le produit sélectionné dans le tableau."""
        if not hasattr(self, 'inventory_tree'): return
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit.")
            return

        item = self.inventory_tree.item(selected[0])
        nom_produit = item['values'][0] # On suppose que le Nom est la 1ère colonne

        if messagebox.askyesno("Confirmation", f"Supprimer {nom_produit} ?"):
            products.delete_product(nom_produit)
            self.show_inventory() # Rafraichir

    def open_add_order_window(self):
        """Fenêtre modale pour créer une commande."""
        win = tk.Toplevel(self)
        win.title("Nouvelle Commande")
        win.geometry("400x350")
        win.configure(bg=COLOR_BG)

        # Chargement des produits pour la liste déroulante
        df_prods = pd.read_csv("csv/products.csv")
        product_list = df_prods["Nom"].tolist() if not df_prods.empty else []

        tk.Label(win, text="Nom Client", bg=COLOR_BG).pack(pady=5)
        e_client = tk.Entry(win)
        e_client.insert(0, "admin") # Valeur par défaut
        e_client.pack()

        tk.Label(win, text="Produit", bg=COLOR_BG).pack(pady=5)
        cb_prod = ttk.Combobox(win, values=product_list)
        cb_prod.pack()

        tk.Label(win, text="Quantité (Chiffres uniquement)", bg=COLOR_BG).pack(pady=5)
        e_qty = tk.Entry(win)
        e_qty.pack()

        def save_order():
            client = e_client.get().strip()
            prod = cb_prod.get().strip()
            qty_str = e_qty.get().strip()

            # Validation Quantité simple (évite l'import regex)
            if not qty_str.isdigit():
                 messagebox.showerror("Erreur de validation", "La quantité doit être un nombre entier positif.")
                 return

            try:
                qty = int(qty_str)

                # Utilisation de la logique métier orders.py
                # Note: create_order gère la vérification du stock
                orders.create_order(client, prod, qty)
                
                messagebox.showinfo("Succès", "Commande validée !")
                win.destroy()
                self.show_orders() # Rafraichir
                
            except ValueError as e:
                 messagebox.showerror("Erreur", str(e))
            except Exception as e:
                 # orders.create_order peut lever des prints ou erreurs non capturées
                 # Idéalement orders.py devrait lever des exceptions claires
                 # Vérifions si create_order retourne qqchose ou raise
                 messagebox.showerror("Erreur", "Vérifiez le stock ou les données.")

        tk.Button(win, text="Valider Commande", bg=COLOR_SUCCESS, fg="white", command=save_order).pack(pady=20)


    def _create_treeview(self, df):
        """Utilitaire pour créer un tableau de données à partir d'un DataFrame pandas."""
        frame = tk.Frame(self.container, bg="white")
        frame.pack(fill="both", expand=True)

        cols = list(df.columns)
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center", width=120)

        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))

        tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        
        return tree

    def show_messages(self):
        """Affiche la messagerie interne."""
        self.clear_view()
        
        # Header
        header_frame = tk.Frame(self.container, bg=COLOR_BG)
        header_frame.pack(fill="x", pady=(0, 20))

        tk.Label(header_frame, text=f"Messagerie - {self.current_user}", font=("Segoe UI", 18, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(side="left")

        try:
            df = pd.read_csv("csv/messages.csv")
            
            # Gestion de la colonne expéditeur (rétrocompatibilité)
            if "Sender" not in df.columns:
                df["Sender"] = "Système"

            # On filtre les messages destinés à l'utilisateur actuel
            if "User" in df.columns:
                my_msgs = df[df["User"] == self.current_user]
                
                # On garde Expéditeur et Message. User (soi-même) est implicite.
                my_msgs = my_msgs[["Sender", "Message"]]
                my_msgs.columns = ["Expéditeur", "Message"]
            else:
                my_msgs = df

            if my_msgs.empty:
                tk.Label(self.container, text="Aucun message reçu.", bg=COLOR_BG, fg="#7f8c8d", font=("Segoe UI", 12)).pack(pady=20)
            else:
                self._create_treeview(my_msgs)
        except Exception as e:
            tk.Label(self.container, text=f"Erreur chargement messages : {e}", fg="red").pack()

    def open_send_message_window(self):
        """Fenêtre pour envoyer un message."""
        win = tk.Toplevel(self)
        win.title("Nouveau Message")
        win.geometry("400x350")
        win.configure(bg=COLOR_BG)
        
        # Liste des destinataires
        users = []
        try:
            users_df = pd.read_csv("csv/users.csv")
            users = users_df["Username"].tolist()
        except:
            pass

        tk.Label(win, text="Destinataire", bg=COLOR_BG).pack(pady=5)
        # On empêche de s'envoyer un message à soi-même (optionnel mais UX++)
        users = [u for u in users if u != self.current_user]
        cb_dest = ttk.Combobox(win, values=users)
        cb_dest.pack()
        
        tk.Label(win, text="Message", bg=COLOR_BG).pack(pady=5)
        txt_msg = tk.Text(win, height=8, width=40)
        txt_msg.pack(pady=5)
        
        def send():
            dest = cb_dest.get()
            msg = txt_msg.get("1.0", "end-1c").strip()
            
            if dest and msg:
                try:
                    # On passe self.current_user comme expéditeur
                    auth.send_message(dest, msg, self.current_user)
                    messagebox.showinfo("Succès", "Message envoyé !", parent=win)
                    win.destroy()
                    self.show_messages() # Rafraichir
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur d'envoi : {e}", parent=win)
            else:
                messagebox.showerror("Erreur", "Veuillez remplir le destinataire et le message.", parent=win)

        tk.Button(win, text="Envoyer", bg=COLOR_SUCCESS, fg="white", command=send).pack(pady=10)

    def show_admin_panel(self):
        """Affiche le panneau d'administration (Liste des utilisateurs)."""
        self.clear_view()
        tk.Label(self.container, text="Administration - Gestion des Utilisateurs", font=("Segoe UI", 18, "bold"), 
                 bg=COLOR_BG, fg=COLOR_PRIMARY).pack(anchor="w", pady=(0, 20))

        try:
            # Rechargement frais des utilisateurs
            users_df = auth.load_users()
            # On masque le mot de passe pour sécurité (même si c'est hashé)
            if 'PasswordHash' in users_df.columns:
                 users_df['PasswordHash'] = "********"
            
            self._create_treeview(users_df)
        except Exception as e:
            tk.Label(self.container, text=f"Erreur chargement utilisateurs : {e}", fg="red").pack()

    def _not_implemented(self, name):
        messagebox.showinfo("Module ERP", f"Le module {name} est actuellement en cours de développement.")

if __name__ == "__main__":
    app = ERPApplication()
    app.mainloop()
